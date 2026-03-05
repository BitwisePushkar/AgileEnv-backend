from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from fastapi import HTTPException, status as http_status
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from app.scrum.model import (Epic, Sprint, ScrumIssue, IssueComment, EpicStatus, SprintStatus,
                             IssueType, IssueStatus, IssuePriority,)
from app.scrum import schemas
from app.project.model import Project
from app.project.crud import is_project_member
from datetime import timezone as _tz
from app.auth.models import User
import logging

logger = logging.getLogger(__name__)

ORDER_STEP = 1000.0

def assert_scrum_project(project: Project) -> None:
    if project.board_type.value != "scrum":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,detail=f"This project uses {project.board_type.value.title()}, not Scrum",)

def _next_backlog_order(db: Session, project_id: int) -> float:
    max_val = (db.query(func.max(ScrumIssue.order)).filter(ScrumIssue.project_id == project_id, ScrumIssue.sprint_id.is_(None))
               .scalar())
    return (max_val or 0) + ORDER_STEP

def _next_sprint_order(db: Session, sprint_id: int) -> float:
    max_val = (db.query(func.max(ScrumIssue.order)).filter(ScrumIssue.sprint_id == sprint_id).scalar())
    return (max_val or 0) + ORDER_STEP

def get_epic_or_404(db: Session, epic_id: int) -> Epic:
    epic = db.get(Epic, epic_id)
    if not epic:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Epic not found")
    return epic

def get_sprint_or_404(db: Session, sprint_id: int) -> Sprint:
    sprint = db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Sprint not found")
    return sprint

def get_issue_or_404(db: Session, issue_id: int) -> ScrumIssue:
    issue = (db.query(ScrumIssue).options(joinedload(ScrumIssue.assignee).joinedload(User.profile),joinedload(ScrumIssue.reporter).joinedload(User.profile),
                                           joinedload(ScrumIssue.subtasks).joinedload(ScrumIssue.assignee).joinedload(User.profile),
                                           joinedload(ScrumIssue.comments).joinedload(IssueComment.author).joinedload(User.profile),
                                           joinedload(ScrumIssue.epic),joinedload(ScrumIssue.sprint),).filter(ScrumIssue.id == issue_id).first())
    if not issue:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Issue not found")
    return issue

def get_comment_or_404(db: Session, comment_id: int) -> IssueComment:
    comment = (db.query(IssueComment).options(joinedload(IssueComment.author).joinedload(User.profile))
               .filter(IssueComment.id == comment_id).first())
    if not comment:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Comment not found")
    return comment

def get_effective_points(db: Session, issue: ScrumIssue) -> Optional[int]:
    if issue.type == IssueType.STORY:
        total = (db.query(func.sum(ScrumIssue.story_points)).filter(ScrumIssue.parent_id == issue.id, ScrumIssue.story_points.isnot(None))
                 .scalar())
        if total is not None:
            return int(total)
    return issue.story_points

def create_epic(db: Session, project_id: int, data: schemas.EpicCreate, creator_id: int) -> Epic:
    epic = Epic(project_id = project_id,
                title = data.title,
                description = data.description,
                color = data.color,
                start_date = data.start_date,
                end_date = data.end_date,
                created_by = creator_id,)
    db.add(epic)
    db.commit()
    db.refresh(epic)
    return epic

def list_epics(db: Session, project_id: int) -> List[Epic]:
    return (db.query(Epic).filter(Epic.project_id == project_id).order_by(Epic.created_at.desc()).all())

def get_epic_with_issues(db: Session, epic_id: int) -> Epic:
    epic = (db.query(Epic).options(joinedload(Epic.issues).joinedload(ScrumIssue.assignee).joinedload(User.profile),)
            .filter(Epic.id == epic_id).first())
    if not epic:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Epic not found")
    return epic

def update_epic(db: Session, epic: Epic, data: schemas.EpicUpdate) -> Epic:
    def _tz_aware(dt):
        return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=_tz.utc)
    updates = data.model_dump(exclude_unset=True)
    new_start = _tz_aware(updates.get("start_date", epic.start_date))
    new_end = _tz_aware(updates.get("end_date",   epic.end_date))
    if new_start and new_end and new_end <= new_start:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"end_date ({new_end.date()}) must be after start_date ({new_start.date()})",)
    if new_start:
        from datetime import datetime as _dt
        today = _dt.now(_tz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if new_start < today:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"start_date cannot be in the past (got {new_start.date()}, today is {today.date()})",)
    for field, value in updates.items():
        setattr(epic, field, value)
    db.commit()
    db.refresh(epic)
    return epic

def update_epic_status(db: Session, epic: Epic, new_status: str) -> Epic:
    epic.status = EpicStatus(new_status)
    db.commit()
    db.refresh(epic)
    return epic

def delete_epic(db: Session, epic: Epic) -> None:
    db.delete(epic)
    db.commit()

def get_epic_progress(db: Session, epic_id: int) -> schemas.EpicProgress:
    base = (db.query(ScrumIssue).filter(ScrumIssue.epic_id == epic_id, ScrumIssue.parent_id.is_(None)))
    total_issues = base.count()
    done_issues  = base.filter(ScrumIssue.status == IssueStatus.DONE).count()
    total_points = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
                    .filter(ScrumIssue.epic_id == epic_id, ScrumIssue.parent_id.is_(None),ScrumIssue.story_points.isnot(None))
                    .scalar() or 0)
    done_points = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
                   .filter(ScrumIssue.epic_id == epic_id, ScrumIssue.parent_id.is_(None),
                           ScrumIssue.status == IssueStatus.DONE, ScrumIssue.story_points.isnot(None)).scalar() or 0)
    issue_progress = round(done_issues / total_issues, 4) if total_issues  else 0.0
    points_progress = round(done_points / total_points, 4) if total_points  else 0.0
    return schemas.EpicProgress(epic_id = epic_id,
                                total_issues = total_issues,
                                done_issues = done_issues,
                                total_points = int(total_points),
                                done_points = int(done_points),
                                issue_progress = issue_progress,
                                points_progress = points_progress,)

def create_sprint(db: Session, project_id: int, data: schemas.SprintCreate) -> Sprint:
    sprint = Sprint(project_id=project_id, name=data.name, goal=data.goal)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint

def list_sprints(db: Session, project_id: int) -> List[Sprint]:
    return (db.query(Sprint).filter(Sprint.project_id == project_id).order_by(Sprint.created_at.desc()).all())

def get_sprint_with_issues(db: Session, sprint_id: int) -> Sprint:
    sprint = (db.query(Sprint).options(joinedload(Sprint.issues).joinedload(ScrumIssue.assignee).joinedload(User.profile),)
              .filter(Sprint.id == sprint_id).first())
    if not sprint:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Sprint not found")
    return sprint

def update_sprint(db: Session, sprint: Sprint, data: schemas.SprintUpdate) -> Sprint:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)
    return sprint

def start_sprint(db: Session, sprint: Sprint, data: schemas.SprintStart) -> Sprint:
    if sprint.status != SprintStatus.PLANNING:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Only 'planning' sprints can be started.",)
    active = (db.query(Sprint).filter(Sprint.project_id == sprint.project_id, Sprint.status == SprintStatus.ACTIVE)
              .first())
    if active:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Sprint '{active.name}' is already active. Complete it before starting a new one.",)
    issue_count = db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id).count()
    if issue_count == 0:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Cannot start an empty sprint. Add at least one issue first.",)
    sprint.status = SprintStatus.ACTIVE
    sprint.start_date = data.start_date
    sprint.end_date = data.end_date
    db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id,ScrumIssue.status == IssueStatus.BACKLOG,
                                ).update({"status": IssueStatus.TODO}, synchronize_session="fetch")
    db.commit()
    db.refresh(sprint)
    return sprint

def complete_sprint(db: Session, sprint: Sprint) -> Sprint:
    if sprint.status != SprintStatus.ACTIVE:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Only 'active' sprints can be completed.",)
    unfinished = (db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id, ScrumIssue.status != IssueStatus.DONE)
                  .all())
    sprint.carried_over_count = len(unfinished)
    for issue in unfinished:
        issue.sprint_id = None
        issue.status = IssueStatus.BACKLOG
    sprint.status = SprintStatus.COMPLETED
    sprint.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sprint)
    return sprint

def delete_sprint(db: Session, sprint: Sprint) -> None:
    if sprint.status != SprintStatus.PLANNING:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Only 'planning' sprints can be deleted.",)
    db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id).update({"sprint_id": None, "status": IssueStatus.BACKLOG},
                                                                          synchronize_session="fetch",)
    db.delete(sprint)
    db.commit()

def get_sprint_stats(db: Session, sprint_id: int) -> schemas.SprintStats:
    sprint = get_sprint_or_404(db, sprint_id)
    base = db.query(ScrumIssue).filter(ScrumIssue.sprint_id  == sprint_id,ScrumIssue.parent_id.is_(None),)
    def _count(s: IssueStatus) -> int:
        return base.filter(ScrumIssue.status == s).count()
    total = base.count()
    todo = _count(IssueStatus.TODO)
    in_progress = _count(IssueStatus.IN_PROGRESS)
    in_review = _count(IssueStatus.IN_REVIEW)
    done = _count(IssueStatus.DONE)
    total_points = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
                    .filter(ScrumIssue.sprint_id == sprint_id, ScrumIssue.story_points.isnot(None),ScrumIssue.parent_id.is_(None))
                    .scalar() or 0)
    done_points = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
                   .filter(ScrumIssue.sprint_id == sprint_id, ScrumIssue.status == IssueStatus.DONE,
                           ScrumIssue.story_points.isnot(None), ScrumIssue.parent_id.is_(None)).scalar() or 0)
    completion_pct = round(done_points / total_points, 4) if total_points else 0.0
    return schemas.SprintStats(sprint_id = sprint_id,
                               sprint_name = sprint.name,
                               total = total,
                               todo = todo,
                               in_progress = in_progress,
                               in_review = in_review,
                               done = done,
                               total_points = int(total_points),
                               done_points = int(done_points),
                               completion_pct = completion_pct,)

def add_issue_to_sprint(db: Session, sprint: Sprint, issue: ScrumIssue) -> ScrumIssue:
    if sprint.status == SprintStatus.COMPLETED:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Cannot add issues to a completed sprint.")
    if issue.project_id != sprint.project_id:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Issue does not belong to this project.")
    if issue.type == IssueType.SUBTASK:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Subtasks cannot be added directly to a sprint. Add the parent Story instead.",)
    if issue.sprint_id is not None:
        if issue.sprint_id == sprint.id:
            raise HTTPException(http_status.HTTP_409_CONFLICT, "Issue is already in this sprint.")
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Issue is already in another sprint (id={issue.sprint_id}). Remove it first.",)
    issue.sprint_id = sprint.id
    if sprint.status == SprintStatus.ACTIVE:
        issue.status = IssueStatus.TODO
    if issue.type == IssueType.STORY:
        subtasks = db.query(ScrumIssue).filter(ScrumIssue.parent_id == issue.id).all()
        for subtask in subtasks:
            subtask.sprint_id = sprint.id
            if sprint.status == SprintStatus.ACTIVE:
                subtask.status = IssueStatus.TODO
    db.commit()
    return get_issue_or_404(db, issue.id)

def bulk_add_to_sprint(db: Session, sprint: Sprint, issue_ids: List[int]) -> schemas.BulkAddResult:
    if sprint.status == SprintStatus.COMPLETED:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Cannot add issues to a completed sprint.",)
    added: List[int]  = []
    skipped: List[int]  = []
    failed: List[dict] = []
    for issue_id in issue_ids:
        issue = db.get(ScrumIssue, issue_id)
        if not issue:
            failed.append({"id": issue_id, "reason": "Issue not found"})
            continue
        if issue.project_id != sprint.project_id:
            failed.append({"id": issue_id, "reason": "Issue does not belong to this project"})
            continue
        if issue.type == IssueType.SUBTASK:
            failed.append({"id": issue_id, "reason": "Subtasks cannot be added directly; add the parent Story"})
            continue
        if issue.sprint_id == sprint.id:
            skipped.append(issue_id)
            continue
        if issue.sprint_id is not None:
            failed.append({"id": issue_id, "reason": f"Already in sprint {issue.sprint_id}"})
            continue
        issue.sprint_id = sprint.id
        if sprint.status == SprintStatus.ACTIVE:
            issue.status = IssueStatus.TODO
        if issue.type == IssueType.STORY:
            subtasks = db.query(ScrumIssue).filter(ScrumIssue.parent_id == issue.id).all()
            for subtask in subtasks:
                subtask.sprint_id = sprint.id
                if sprint.status == SprintStatus.ACTIVE:
                    subtask.status = IssueStatus.TODO
        added.append(issue_id)
    db.commit()
    return schemas.BulkAddResult(added=added, skipped=skipped, failed=failed)

def remove_issue_from_sprint(db: Session, sprint: Sprint, issue: ScrumIssue) -> None:
    if sprint.status == SprintStatus.COMPLETED:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Cannot remove issues from a completed sprint.",)
    if issue.sprint_id != sprint.id:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Issue is not in this sprint.")
    issue.sprint_id = None
    issue.status = IssueStatus.BACKLOG
    if issue.type == IssueType.STORY:
        subtasks = db.query(ScrumIssue).filter(ScrumIssue.parent_id == issue.id).all()
        for subtask in subtasks:
            subtask.sprint_id = None
            subtask.status = IssueStatus.BACKLOG
    db.commit()

def create_issue(db: Session, project_id: int, data: schemas.IssueCreate, reporter_id: int) -> ScrumIssue:
    if data.type == "subtask":
        parent = db.get(ScrumIssue, data.parent_id)
        if not parent:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Parent issue not found.")
        if parent.project_id != project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Parent issue does not belong to this project.",)
        if parent.type != IssueType.STORY:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Subtasks can only be children of a Story. Parent is type '{parent.type.value}'.",)
        if data.sprint_id and parent.sprint_id != data.sprint_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Subtask's sprint must match the parent story's sprint. Parent story is in sprint {parent.sprint_id}.",)
    if data.epic_id:
        epic = db.get(Epic, data.epic_id)
        if not epic or epic.project_id != project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Epic not found or does not belong to this project.",)
    sprint_id = None
    initial_status = IssueStatus.BACKLOG
    if data.sprint_id:
        sprint = db.get(Sprint, data.sprint_id)
        if not sprint or sprint.project_id != project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Sprint not found or does not belong to this project.",)
        if sprint.status == SprintStatus.COMPLETED:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Cannot add issues to a completed sprint.",)
        sprint_id = data.sprint_id
        initial_status = (IssueStatus.TODO if sprint.status == SprintStatus.ACTIVE else IssueStatus.BACKLOG)
        if data.due_date and sprint.end_date:
            from datetime import timezone as _tz
            dd = data.due_date  if data.due_date.tzinfo  else data.due_date.replace(tzinfo=_tz.utc)
            se = sprint.end_date if sprint.end_date.tzinfo else sprint.end_date.replace(tzinfo=_tz.utc)
            if dd > se:
                raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"due_date ({data.due_date.date()}) cannot be after the sprint end_date ({sprint.end_date.date()})",)
    if data.assignee_id and not is_project_member(db, project_id, data.assignee_id):
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Assignee must be a member of this project.",)
    order = (_next_sprint_order(db, sprint_id) if sprint_id else _next_backlog_order(db, project_id))
    issue = ScrumIssue(project_id = project_id,
                       epic_id = data.epic_id,
                       sprint_id = sprint_id,
                       parent_id = data.parent_id,
                       title = data.title,
                       description = data.description,
                       type = IssueType(data.type),
                       status = initial_status,
                       priority = IssuePriority(data.priority or "medium"),
                       story_points = data.story_points,
                       assignee_id = data.assignee_id,
                       reporter_id = reporter_id,
                       order = order,
                       due_date = data.due_date,)
    db.add(issue)
    db.commit()
    return get_issue_or_404(db, issue.id)

def get_backlog(db: Session, project_id: int) -> List[ScrumIssue]:
    return (db.query(ScrumIssue).options(joinedload(ScrumIssue.assignee).joinedload(User.profile),joinedload(ScrumIssue.reporter).joinedload(User.profile),
                                         joinedload(ScrumIssue.subtasks),joinedload(ScrumIssue.epic),)
                                         .filter(ScrumIssue.project_id == project_id,ScrumIssue.sprint_id.is_(None),
                                                 ScrumIssue.parent_id.is_(None),ScrumIssue.status == IssueStatus.BACKLOG,)
                                                 .order_by(ScrumIssue.order).all())

def reorder_backlog(db: Session, project_id: int, items: List[schemas.BacklogReorderItem]) -> None:
    issue_ids = [item.issue_id for item in items]
    issues = (db.query(ScrumIssue).filter(ScrumIssue.id.in_(issue_ids)).all())
    issue_map = {i.id: i for i in issues}
    for item in items:
        issue = issue_map.get(item.issue_id)
        if not issue:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND,f"Issue {item.issue_id} not found.",)
        if issue.project_id != project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Issue {item.issue_id} does not belong to this project.",)
        if issue.sprint_id is not None:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Issue {item.issue_id} is in a sprint. Only backlog issues can be reordered here.",)
        issue.order = item.order
    db.commit()

def search_issues(db: Session, project_id: int, filters: schemas.IssueFilterParams) -> List[ScrumIssue]:
    query = (db.query(ScrumIssue).options(joinedload(ScrumIssue.assignee).joinedload(User.profile), 
                                          joinedload(ScrumIssue.reporter).joinedload(User.profile),
                                          joinedload(ScrumIssue.epic),).filter(ScrumIssue.project_id == project_id))
    if filters.type and filters.type == "subtask":
        query = query.filter(ScrumIssue.type == IssueType.SUBTASK)
    elif filters.type:
        query = query.filter(ScrumIssue.type == IssueType(filters.type),ScrumIssue.parent_id.is_(None),)
    else:
        query = query.filter(ScrumIssue.parent_id.is_(None))
    if filters.status:
        query = query.filter(ScrumIssue.status == IssueStatus(filters.status))
    if filters.priority:
        query = query.filter(ScrumIssue.priority == IssuePriority(filters.priority))
    if filters.assignee_id is not None:
        query = query.filter(ScrumIssue.assignee_id == filters.assignee_id)
    if filters.epic_id is not None:
        query = query.filter(ScrumIssue.epic_id == filters.epic_id)
    if filters.sprint_id is not None:
        if filters.sprint_id == 0:
            query = query.filter(ScrumIssue.sprint_id.is_(None))
        else:
            query = query.filter(ScrumIssue.sprint_id == filters.sprint_id)
    if filters.search:
        term = f"%{filters.search.strip()}%"
        query = query.filter(or_(ScrumIssue.title.ilike(term),ScrumIssue.description.ilike(term),))
    return query.order_by(ScrumIssue.order).all()

def update_issue(db: Session, issue: ScrumIssue, data: schemas.IssueUpdate) -> ScrumIssue:
    updates = data.model_dump(exclude_unset=True)
    if "epic_id" in updates and updates["epic_id"] is not None:
        epic = db.get(Epic, updates["epic_id"])
        if not epic or epic.project_id != issue.project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Epic not found or does not belong to this project.",)
        if issue.type == IssueType.SUBTASK:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Subtasks cannot be assigned an epic. The parent story's epic applies.",)
    if "assignee_id" in updates and updates["assignee_id"] is not None:
        if not is_project_member(db, issue.project_id, updates["assignee_id"]):
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Assignee must be a member of this project.",)
    if "priority" in updates and updates["priority"] is not None:
        updates["priority"] = IssuePriority(updates["priority"])
    if "due_date" in updates and updates["due_date"] is not None and issue.sprint_id:
        sprint = db.get(Sprint, issue.sprint_id)
        if sprint and sprint.end_date:
            from datetime import timezone as _tz
            dd = updates["due_date"]
            se = sprint.end_date
            dd = dd if dd.tzinfo else dd.replace(tzinfo=_tz.utc)
            se = se if se.tzinfo else se.replace(tzinfo=_tz.utc)
            if dd > se:
                raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"due_date ({updates['due_date'].date()}) cannot be after the sprint end_date ({sprint.end_date.date()})",)
    for field, value in updates.items():
        setattr(issue, field, value)
    db.commit()
    return get_issue_or_404(db, issue.id)

def update_issue_status(db: Session, issue: ScrumIssue, new_status: str) -> ScrumIssue:
    current = issue.status.value
    allowed = schemas.STATUS_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Cannot transition from '{current}' to '{new_status}'. ")
    issue.status = IssueStatus(new_status)
    if new_status == "done":
        issue.completed_at = datetime.now(timezone.utc)
    elif current == "done" and new_status == "in_progress":
        issue.completed_at = None
        issue.reminders_sent = []
    db.commit()
    return get_issue_or_404(db, issue.id)

def assign_issue(db: Session, issue: ScrumIssue, assignee_id: Optional[int]) -> ScrumIssue:
    if assignee_id is not None and not is_project_member(db, issue.project_id, assignee_id):
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Assignee must be a member of this project.",)
    issue.assignee_id = assignee_id
    db.commit()
    return get_issue_or_404(db, issue.id)

def update_story_points(db: Session, issue: ScrumIssue, points: int) -> ScrumIssue:
    issue.story_points = points
    db.commit()
    return get_issue_or_404(db, issue.id)

def update_issue_epic(db: Session, issue: ScrumIssue, epic_id: Optional[int]) -> ScrumIssue:
    if issue.type == IssueType.SUBTASK:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Subtasks cannot be assigned an epic. The parent story's epic applies.",)
    if epic_id is not None:
        epic = db.get(Epic, epic_id)
        if not epic or epic.project_id != issue.project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Epic not found or does not belong to this project.",)
    issue.epic_id = epic_id
    db.commit()
    return get_issue_or_404(db, issue.id)

def get_subtasks(db: Session, issue_id: int) -> List[ScrumIssue]:
    return (db.query(ScrumIssue).options(joinedload(ScrumIssue.assignee).joinedload(User.profile),
                                         joinedload(ScrumIssue.reporter).joinedload(User.profile),)
                                         .filter(ScrumIssue.parent_id == issue_id)
                                         .order_by(ScrumIssue.order).all())

def delete_issue(db: Session, issue: ScrumIssue) -> None:
    if issue.sprint_id is not None:
        sprint = db.get(Sprint, issue.sprint_id)
        if sprint and sprint.status == SprintStatus.ACTIVE:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Cannot delete an issue in an active sprint. Remove it from the sprint first.",)
    db.delete(issue)
    db.commit()

def create_comment(db: Session, issue_id: int, author_id: int, data: schemas.CommentCreate) -> IssueComment:
    comment = IssueComment(issue_id=issue_id, author_id=author_id, content=data.content)
    db.add(comment)
    db.commit()
    return get_comment_or_404(db, comment.id)

def list_comments(db: Session, issue_id: int) -> List[IssueComment]:
    return (db.query(IssueComment).options(joinedload(IssueComment.author).joinedload(User.profile))
            .filter(IssueComment.issue_id == issue_id).order_by(IssueComment.created_at).all())

def update_comment(db: Session, comment: IssueComment, author_id: int, data: schemas.CommentUpdate) -> IssueComment:
    if comment.author_id != author_id:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN,"Only the comment author can edit this comment.",)
    comment.content  = data.content
    comment.is_edited = True
    db.commit()
    return get_comment_or_404(db, comment.id)

def delete_comment(db: Session, comment: IssueComment, requester_id: int, requester_role: str) -> None:
    is_author = comment.author_id == requester_id
    is_manager = requester_role == "manager"
    if not is_author and not is_manager:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN,"Only the comment author or a project manager can delete this comment.",)
    db.delete(comment)
    db.commit()

def get_active_sprint(db: Session, project_id: int) -> Optional[Sprint]:
    return (db.query(Sprint).filter(Sprint.project_id == project_id, Sprint.status == SprintStatus.ACTIVE)
            .first())

def get_board(db: Session, project_id: int) -> Optional[Sprint]:
    return (db.query(Sprint).options(joinedload(Sprint.issues).joinedload(ScrumIssue.assignee).joinedload(User.profile),)
            .filter(Sprint.project_id == project_id, Sprint.status == SprintStatus.ACTIVE).first())

def get_velocity(db: Session, project_id: int) -> List[dict]:
    sprints = (db.query(Sprint).filter(Sprint.project_id == project_id, Sprint.status == SprintStatus.COMPLETED)
               .order_by(Sprint.completed_at).all())
    result = []
    for sprint in sprints:
        committed = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
                     .filter(ScrumIssue.sprint_id == sprint.id, ScrumIssue.story_points.isnot(None)).scalar() or 0)
        completed = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
                     .filter(ScrumIssue.sprint_id == sprint.id,ScrumIssue.status == IssueStatus.DONE,
                             ScrumIssue.story_points.isnot(None),).scalar() or 0)
        result.append({"sprint_id": sprint.id,
                       "sprint_name": sprint.name,
                       "committed": int(committed),
                       "completed": int(completed),
                       "carried_over_count": sprint.carried_over_count,})
    return result

def get_burndown(db: Session, sprint: Sprint) -> List[dict]:
    if not sprint.start_date:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Sprint has not been started yet.")
    total = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
             .filter(ScrumIssue.sprint_id == sprint.id, ScrumIssue.story_points.isnot(None)).scalar() or 0)
    total = int(total)
    done_issues = (db.query(ScrumIssue.completed_at, ScrumIssue.story_points)
                   .filter(ScrumIssue.sprint_id == sprint.id,ScrumIssue.status == IssueStatus.DONE,
                           ScrumIssue.completed_at.isnot(None),ScrumIssue.story_points.isnot(None),).all())
    today = datetime.now(timezone.utc)
    chart_end = min(sprint.end_date or today, today)
    total_days = max((sprint.end_date.date() - sprint.start_date.date()).days, 1) if sprint.end_date else 1
    days = []
    current = sprint.start_date.astimezone(timezone.utc).date()
    while current <= chart_end.astimezone(timezone.utc).date():
        done_so_far = sum((pts or 0) for completed_at, pts in done_issues
                          if completed_at and completed_at.astimezone(timezone.utc).date() <= current)
        days_elapsed = (current - sprint.start_date.astimezone(timezone.utc).date()).days
        ideal = total * (1 - days_elapsed / total_days)
        days.append({"date": current.isoformat(),"remaining": max(total - done_so_far, 0),"ideal": round(ideal, 2),})
        current += timedelta(days=1)
    return days

def get_project_summary(db: Session, project_id: int) -> dict:
    total_epics = db.query(Epic).filter(Epic.project_id == project_id).count()
    total_sprints = db.query(Sprint).filter(Sprint.project_id == project_id).count()
    active_sprint = get_active_sprint(db, project_id)
    open_issues = (db.query(ScrumIssue).filter(ScrumIssue.project_id == project_id,ScrumIssue.status != IssueStatus.DONE,
                                                ScrumIssue.parent_id.is_(None),).count())
    done_issues = (db.query(ScrumIssue).filter(ScrumIssue.project_id == project_id,ScrumIssue.status == IssueStatus.DONE,
                                               ScrumIssue.parent_id.is_(None),).count())
    total_points = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
                    .filter(ScrumIssue.project_id == project_id, ScrumIssue.story_points.isnot(None)).scalar() or 0)
    done_points = (db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0))
                   .filter(ScrumIssue.project_id == project_id,ScrumIssue.status == IssueStatus.DONE,
                           ScrumIssue.story_points.isnot(None),).scalar() or 0)
    velocity_data = get_velocity(db, project_id)
    avg_velocity = (sum(v["completed"] for v in velocity_data) / len(velocity_data) if velocity_data else 0.0)
    return {"project_id": project_id,
            "total_epics": total_epics,
            "total_sprints": total_sprints,
            "active_sprint": active_sprint,
            "open_issues": open_issues,
            "done_issues": done_issues,
            "total_points": int(total_points),
            "done_points": int(done_points),
            "average_velocity": round(avg_velocity, 1),}