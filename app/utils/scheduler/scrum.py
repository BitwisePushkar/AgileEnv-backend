from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import logging
from app.scrum.model import (ScrumIssue, Sprint, IssueStatus, SprintStatus,)
from app.project.model import Project
from app.workspace.model import WorkspaceMember
from app.auth.models import Profile, User
from app.utils.email.scrum import (send_scrum_issue_deadline_72h,send_scrum_issue_deadline_24h,send_scrum_issue_deadline_2h,
                                   send_scrum_issue_overdue_assignee,send_scrum_issue_overdue_reporter,send_scrum_sprint_ending_soon,)

logger = logging.getLogger(__name__)

_MILESTONES = [
    ("72h", 72, 71), 
    ("24h", 24, 23), 
    ("2h",   2,  1), 
]

_ACTIVE_STATUSES = [IssueStatus.TODO, IssueStatus.IN_PROGRESS, IssueStatus.IN_REVIEW]

def _get_profile(db: Session, user_id: int) -> Profile:
    return db.query(Profile).filter(Profile.user_id == user_id).first()

def _fmt_due_date(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

def _run_issue_reminders(db: Session) -> int:
    now = datetime.now(timezone.utc)
    sent_count = 0
    upcoming = (db.query(ScrumIssue).options(joinedload(ScrumIssue.assignee),joinedload(ScrumIssue.project),)
                .filter(ScrumIssue.status.in_(_ACTIVE_STATUSES),ScrumIssue.due_date.isnot(None),ScrumIssue.assignee_id.isnot(None),
                        ScrumIssue.due_date > now,ScrumIssue.due_date <= now + timedelta(hours=73),).all())

    for issue in upcoming:
        sent_list = issue.reminders_sent or []
        hours_until = (issue.due_date - now).total_seconds() / 3600
        project_name = issue.project.name if issue.project else "your project"
        due_str = _fmt_due_date(issue.due_date)
        modified = False

        for key, upper, lower in _MILESTONES:
            if key in sent_list:
                continue  
            if not (lower < hours_until <= upper):
                continue  
            assignee = issue.assignee
            assignee_profile = _get_profile(db, assignee.id)
            lang = assignee_profile.language if assignee_profile else "en"
            username = assignee.username or assignee.email
            fn = {"72h": send_scrum_issue_deadline_72h,
                  "24h": send_scrum_issue_deadline_24h,
                  "2h":  send_scrum_issue_deadline_2h, }[key]
            ok = fn(email = assignee.email,
                    username = username,
                    issue_title = issue.title,
                    project_name = project_name,
                    due_date = due_str,
                    language = lang,)
            if ok:
                sent_list = sent_list + [key]
                sent_count += 1
                modified = True
                logger.info(f"Scrum reminder [{key}] | issue_id={issue.id} | assignee={assignee.email[:4]}***")
        if modified:
            issue.reminders_sent = sent_list
            db.add(issue)
    if sent_count:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit scrum upcoming reminder updates: {e}")
    overdue = (db.query(ScrumIssue).options(joinedload(ScrumIssue.assignee),joinedload(ScrumIssue.reporter),
                                            joinedload(ScrumIssue.project),)
                                            .filter( ScrumIssue.status.in_(_ACTIVE_STATUSES),ScrumIssue.due_date.isnot(None), 
                                                    ScrumIssue.due_date < now,).all())
    overdue_modified = False
    for issue in overdue:
        sent_list = issue.reminders_sent or []
        if "overdue" in sent_list:
            continue
        project_name = issue.project.name if issue.project else "your project"
        due_str = _fmt_due_date(issue.due_date)
        card_sent = False
        if issue.assignee_id and issue.assignee:
            assignee = issue.assignee
            profile = _get_profile(db, assignee.id)
            lang = profile.language if profile else "en"
            ok = send_scrum_issue_overdue_assignee(email = assignee.email,
                                                   username = assignee.username or assignee.email,
                                                   issue_title = issue.title,
                                                   project_name = project_name,
                                                   due_date = due_str,
                                                   language = lang,)
            if ok:
                sent_count += 1
                card_sent = True
                logger.info(f"Scrum overdue [assignee] | issue_id={issue.id} | assignee={assignee.email[:4]}***")
        if issue.reporter_id and issue.reporter and issue.reporter_id != issue.assignee_id:
            reporter = issue.reporter
            profile = _get_profile(db, reporter.id)
            lang = profile.language if profile else "en"
            ok = send_scrum_issue_overdue_reporter(email = reporter.email,
                                                   username = reporter.username or reporter.email,
                                                   issue_title = issue.title,
                                                   project_name = project_name,
                                                   due_date = due_str,
                                                   language = lang,)
            if ok:
                sent_count   += 1
                card_sent = True
                logger.info(f"Scrum overdue [reporter] | issue_id={issue.id} | reporter={reporter.email[:4]}***")
        if card_sent:
            issue.reminders_sent = sent_list + ["overdue"]
            overdue_modified = True
            db.add(issue)
    if overdue_modified:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit scrum overdue reminder updates: {e}")
    return sent_count

def _run_sprint_end_warnings(db: Session) -> int:
    now = datetime.now(timezone.utc)
    sent_count = 0
    window_start = now + timedelta(hours=48)
    window_end = now + timedelta(hours=49)
    at_risk_sprints = (db.query(Sprint).options(joinedload(Sprint.project))
                       .filter(Sprint.status == SprintStatus.ACTIVE,Sprint.end_warning_sent == False,
                               Sprint.end_date.isnot(None),Sprint.end_date >= window_start,
                               Sprint.end_date < window_end,).all())
    for sprint in at_risk_sprints:
        project = sprint.project
        if not project:
            continue
        admin_member = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == project.workspace_id,
                                                         WorkspaceMember.role == "admin",).first())
        if not admin_member:
            logger.warning(f"Sprint {sprint.id} end warning skipped — no admin found for workspace {project.workspace_id}")
            continue
        admin_user = db.get(User, admin_member.user_id)
        if not admin_user:
            continue
        admin_profile = _get_profile(db, admin_user.id)
        lang = admin_profile.language if admin_profile else "en"
        open_count = (db.query(func.count(ScrumIssue.id)).filter(ScrumIssue.sprint_id == sprint.id,ScrumIssue.status != IssueStatus.DONE,
                                                                 ScrumIssue.parent_id.is_(None),).scalar() or 0)
        end_str = _fmt_due_date(sprint.end_date)
        ok = send_scrum_sprint_ending_soon(email = admin_user.email,
                                           username = admin_user.username or admin_user.email,
                                           sprint_name = sprint.name,
                                           project_name = project.name,
                                           end_date = end_str,
                                           open_count = open_count,
                                           language = lang,)
        if ok:
            sprint.end_warning_sent = True
            db.add(sprint)
            sent_count += 1
            logger.info(f"Sprint end warning sent | sprint_id={sprint.id} | manager={admin_user.email[:4]}***")
    if sent_count:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit sprint end_warning_sent updates: {e}")
    return sent_count

def send_scrum_scheduled_notifications(db: Session) -> int:
    total = 0
    total += _run_issue_reminders(db)
    total += _run_sprint_end_warnings(db)
    return total