from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone, timedelta
from app.utils.dbUtil import SessionLocal
from app.utils.scheduler.kanban import send_kanban_deadline_reminders
from app.utils.scheduler.scrum  import send_scrum_scheduled_notifications
import logging

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone="UTC")

def _run_kanban_reminders() -> None:
    db = SessionLocal()
    try:
        sent = send_kanban_deadline_reminders(db)
        if sent:
            logger.info(f"Kanban reminders: sent {sent} email(s) this run")
    except Exception as e:
        logger.error(f"Kanban reminder job failed: {e}", exc_info=True)
    finally:
        db.close()

def _run_scrum_notifications() -> None:
    db = SessionLocal()
    try:
        sent = send_scrum_scheduled_notifications(db)
        if sent:
            logger.info(f"Scrum notifications: sent {sent} email(s) this run")
    except Exception as e:
        logger.error(f"Scrum notification job failed: {e}", exc_info=True)
    finally:
        db.close()

def start_scheduler() -> None:
    _scheduler.add_job(
        func = _run_kanban_reminders,
        trigger = IntervalTrigger(minutes=5),
        id = "kanban_deadline_reminders",
        name = "Kanban deadline reminder emails",
        replace_existing = True,
        max_instances = 1,   
        misfire_grace_time= 300, 
    )

    scrum_first_run = datetime.now(timezone.utc) + timedelta(seconds=30)
    _scheduler.add_job(
        func = _run_scrum_notifications,
        trigger = IntervalTrigger(minutes=5, start_date=scrum_first_run),
        id = "scrum_scheduled_notifications",
        name = "Scrum deadline reminders and sprint end warnings",
        replace_existing = True,
        max_instances = 1,
        misfire_grace_time= 300,
    )
    _scheduler.start()
    logger.info("Scheduler started — kanban reminders and scrum notifications running every 5 minute"
    )

def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")