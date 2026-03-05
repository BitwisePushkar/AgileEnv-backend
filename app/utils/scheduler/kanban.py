from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
import logging
from app.kanban.models import KanbanCard, CardStatus
from app.auth.models import Profile
from app.utils.email.kanban import (send_kanban_deadline_72h,send_kanban_deadline_24h,send_kanban_deadline_2h,
                                    send_kanban_overdue_assignee,send_kanban_overdue_creator,)

logger = logging.getLogger(__name__)

_MILESTONES = [
    ("72h", 72, 1),  
    ("24h", 24, 1),  
    ("2h",   2, 1), 
]

def _get_profile(db: Session, user_id: int) -> Profile:
    return db.query(Profile).filter(Profile.user_id == user_id).first()

def _format_due_date(dt: datetime) -> str:
    return dt.strftime("%B %d, %Y at %H:%M UTC")

def send_kanban_deadline_reminders(db: Session) -> int:
    now = datetime.now(timezone.utc)
    sent_count = 0
    upcoming_cards = (db.query(KanbanCard).options(joinedload(KanbanCard.assignee),joinedload(KanbanCard.creator),joinedload(KanbanCard.project),)
                      .filter(KanbanCard.is_archived == False,KanbanCard.status.in_([CardStatus.ACTIVE, CardStatus.REOPENED]),
                              KanbanCard.due_date.isnot(None),KanbanCard.assignee_id.isnot(None),KanbanCard.due_date > now,
                              KanbanCard.due_date <= now + timedelta(hours=73),).all())
    for card in upcoming_cards:
        reminders_sent = card.reminders_sent or []
        time_until_due = (card.due_date - now).total_seconds() / 3600 
        for milestone_key, hours_before, window in _MILESTONES:
            if milestone_key in reminders_sent:
                continue 
            lower = hours_before - window
            upper = hours_before
            if not (lower < time_until_due <= upper):
                continue
            assignee = card.assignee
            if not assignee:
                continue
            assignee_profile = _get_profile(db, assignee.id)
            lang = assignee_profile.language if assignee_profile else "en"
            username = assignee.username or assignee.email
            due_str = _format_due_date(card.due_date)
            project_name = card.project.name if card.project else "your project"
            success = False
            if milestone_key == "72h":
                success = send_kanban_deadline_72h(email=assignee.email, username=username,card_title=card.title,
                                                   project_name=project_name,due_date=due_str, language=lang,)
            elif milestone_key == "24h":
                success = send_kanban_deadline_24h(email=assignee.email, username=username,card_title=card.title,
                                                   project_name=project_name,due_date=due_str, language=lang,)
            elif milestone_key == "2h":
                success = send_kanban_deadline_2h(email=assignee.email, username=username, card_title=card.title,
                                                  project_name=project_name, due_date=due_str, language=lang,)
            if success:
                card.reminders_sent = reminders_sent + [milestone_key]
                reminders_sent = card.reminders_sent  
                db.add(card)
                sent_count += 1
                logger.info(f"Reminder [{milestone_key}] sent | card_id={card.id} | assignee={assignee.email[:4]}***")
    if sent_count > 0:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit reminder_sent updates: {e}")

    overdue_cards = (db.query(KanbanCard).options(joinedload(KanbanCard.assignee),joinedload(KanbanCard.creator),joinedload(KanbanCard.project),)
                     .filter(KanbanCard.is_archived == False,KanbanCard.status.in_([CardStatus.ACTIVE, CardStatus.REOPENED]),
                             KanbanCard.due_date.isnot(None),KanbanCard.due_date < now,).all())
    overdue_commits_needed = False
    for card in overdue_cards:
        reminders_sent = card.reminders_sent or []
        if "overdue" in reminders_sent:
            continue 
        due_str = _format_due_date(card.due_date)
        project_name = card.project.name if card.project else "your project"
        card_sent = False
        if card.assignee_id and card.assignee:
            assignee = card.assignee
            assignee_profile = _get_profile(db, assignee.id)
            lang = assignee_profile.language if assignee_profile else "en"
            ok = send_kanban_overdue_assignee(email = assignee.email,
                                              username = assignee.username or assignee.email,
                                              card_title = card.title,
                                              project_name = project_name,
                                              due_date = due_str,
                                              language = lang,)
            if ok:
                sent_count += 1
                card_sent = True
                logger.info(f"Overdue [assignee] sent | card_id={card.id} | assignee={assignee.email[:4]}***")
        if card.created_by and card.creator:
            creator = card.creator
            if creator.id != card.assignee_id:
                creator_profile = _get_profile(db, creator.id)
                lang = creator_profile.language if creator_profile else "en"
                ok = send_kanban_overdue_creator(email = creator.email,
                                                 username = creator.username or creator.email,
                                                 card_title = card.title,
                                                 project_name = project_name,
                                                 due_date = due_str,
                                                 language = lang,)
                if ok:
                    sent_count += 1
                    card_sent = True
                    logger.info(f"Overdue [creator] sent | card_id={card.id} | creator={creator.email[:4]}***")
        if card_sent:
            card.reminders_sent = reminders_sent + ["overdue"]
            overdue_commits_needed = True
            db.add(card)
    if overdue_commits_needed:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit overdue reminder_sent updates: {e}")
    return sent_count