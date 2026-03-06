from celery import Celery
from celery.schedules import crontab
from app.utils.settings import settings

_REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

celery_app = Celery("agile_app",
                    broker = _REDIS_URL,
                    backend = _REDIS_URL,
                    include = ["app.utils.email.email_tasks"],)

celery_app.conf.update(
    task_serializer = "json",
    result_serializer = "json",
    accept_content = ["json"],
    timezone = "UTC",
    enable_utc = True,
    result_expires = 86_400,
    task_max_retries = 3,
    task_default_queue = "emails",
    task_routes = {
        "app.utils.email.email_tasks.send_otp_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_workspace_invite_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_workspace_welcome_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_workspace_invite_new_user_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_project_member_added_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_project_member_removed_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_kanban_assigned_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_kanban_completed_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_kanban_reopened_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_scrum_assigned_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_scrum_sprint_started_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_scrum_sprint_completed_task": {"queue": "emails"},
        "app.utils.email.email_tasks.send_scrum_issue_reopened_task": {"queue": "emails"},
        "app.utils.email.email_tasks.run_kanban_reminders_task": {"queue": "reminders"},
        "app.utils.email.email_tasks.run_scrum_reminders_task": {"queue": "reminders"},    
    },
    beat_schedule = {
        "kanban-deadline-reminders": {
            "task": "app.utils.email.email_tasks.run_kanban_reminders_task",
            "schedule": 300,      
            "options": {"queue": "reminders"},
        },
        "scrum-scheduled-notifications": {
            "task": "app.utils.email.email_tasks.run_scrum_reminders_task",
            "schedule": 300,
            "options":  {"queue": "reminders", "countdown": 30}, 
        },
    },
)