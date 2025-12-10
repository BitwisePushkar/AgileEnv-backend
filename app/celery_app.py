from celery import Celery
from app.config import Settings

settings =  Settings()

celery_app = Celery (
    "Alige Backend",
    broker = settings.REDIS_URL,
    backend =  settings.REDIS_URL,
    include = ['app.tasks.email_tasks']
)
celery_app.conf.update(
    task_serializer = 'json',
    accept_content = 'json',
    result_serializer = 'json',
    timezone = 'UTC',
    enable_utc= True
)