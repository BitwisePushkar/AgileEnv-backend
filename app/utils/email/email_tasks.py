from app.utils.celeryUtil import celery_app
import logging
import smtplib
import app.auth.models        
import app.workspace.model     
import app.project.model       
import app.kanban.models       
import app.scrum.model         
import app.chat.models
import app.whiteboard.model     
from app.whiteboard.crud import prune_old_history
from app.utils.email.otp import send_otp_email
from app.utils.email.workspace import workspace_invitation_new_user,workspace_invitation,workspace_welcome
from app.utils.email.project import send_project_member_added, send_project_member_removed
from app.utils.email.kanban import send_kanban_card_assigned, send_kanban_card_completed, send_kanban_card_reopened
from app.utils.email.scrum import (send_scrum_issue_assigned, send_scrum_sprint_started, send_scrum_sprint_completed,
                                   send_scrum_issue_reopened)
from app.utils.scheduler.kanban import send_kanban_deadline_reminders
from app.utils.scheduler.scrum  import send_scrum_scheduled_notifications
from app.utils.dbUtil import SessionLocal

logger = logging.getLogger(__name__)

_RETRYABLE_EXCEPTIONS = (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, smtplib.SMTPException,
                         TimeoutError, ConnectionError, OSError,)

_RETRY_BACKOFF = True    
_RETRY_DELAYS = [60, 300, 1800]
_MAX_RETRIES = 3

def _log_final_failure(task_name: str, to_email: str, exc: Exception) -> None:
    masked = to_email[:4] + "***" if len(to_email) > 4 else "***"
    logger.error(f"[CELERY FINAL FAILURE] Task={task_name} | Recipient={masked} | Error={type(exc).__name__}: {exc}")

@celery_app.task(bind = True,name = "app.utils.email.email_tasks.send_otp_task",max_retries = _MAX_RETRIES,
             autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, retry_jitter = True, acks_late = True,)
def send_otp_task(self, email: str, otp: str, purpose: str, username: str = "User", language: str = "en",) -> dict:
    try:
        ok = send_otp_email(email = email, otp = otp, purpose = purpose, username = username,language = language,)
        if not ok:
            raise smtplib.SMTPException(f"send_otp_email returned False for purpose={purpose}")
        logger.info(f"OTP email sent | purpose={purpose} | to={email[:4]}***")
        return {"success": True, "purpose": purpose}
    except _RETRYABLE_EXCEPTIONS as exc:
        raise
    except Exception as exc:
        _log_final_failure("send_otp_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_workspace_invite_task", max_retries = _MAX_RETRIES,
             autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, retry_jitter = True, acks_late = True,)
def send_workspace_invite_task(self, email: str, name: str, code: str, admin: str, language: str = "en",) -> dict:
    try:
        ok = workspace_invitation(email = email, name = name, code = code, admin = admin, language = language,)
        if not ok:
            raise smtplib.SMTPException("workspace_invitation returned False")
        logger.info(f"Workspace invite sent | workspace={name} | to={email[:4]}***")
        return {"success": True, "workspace": name}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_workspace_invite_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_workspace_welcome_task", max_retries = _MAX_RETRIES,
              autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, retry_jitter = True, acks_late = True,)
def send_workspace_welcome_task(self, email: str, username: str, workspace_name: str, workspace_description: str,
                                admin_username: str, member_count: int, joined_at: str,) -> dict:
    try:
        ok = workspace_welcome(email = email, username = username, workspace_name = workspace_name,
                               workspace_description = workspace_description, admin_username = admin_username,
                               member_count = member_count, joined_at = joined_at,)
        if not ok:
            raise smtplib.SMTPException("workspace_welcome returned False")
        logger.info(f"Workspace welcome sent | workspace={workspace_name} | to={email[:4]}***")
        return {"success": True, "workspace": workspace_name}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_workspace_welcome_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_kanban_assigned_task", max_retries = _MAX_RETRIES,
              autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, retry_jitter = True, acks_late = True,)
def send_kanban_assigned_task(self, email: str, username: str, card_title: str, project_name: str,
                               language: str = "en",) -> dict:
    try:
        ok = send_kanban_card_assigned(email = email, username = username, card_title = card_title,
                                        project_name = project_name, language = language,)
        if not ok:
            raise smtplib.SMTPException("send_kanban_card_assigned returned False")
        logger.info(f"Kanban assigned email sent | card={card_title} | to={email[:4]}***")
        return {"success": True, "card": card_title}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_kanban_assigned_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_kanban_completed_task", max_retries = _MAX_RETRIES,
             autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, retry_jitter = True, acks_late = True,)
def send_kanban_completed_task(self, email: str, username: str, card_title: str, project_name: str,
                                language: str = "en",) -> dict:
    try:
        ok = send_kanban_card_completed(email = email, username = username, card_title = card_title, 
                                        project_name = project_name, language = language,)
        if not ok:
            raise smtplib.SMTPException("send_kanban_card_completed returned False")
        logger.info(f"Kanban completed email sent | card={card_title} | to={email[:4]}***")
        return {"success": True, "card": card_title}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_kanban_completed_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_kanban_reopened_task", max_retries = _MAX_RETRIES,
              autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, retry_jitter = True, acks_late = True,)
def send_kanban_reopened_task(self, email: str, username: str, card_title: str, project_name: str,
                               language: str = "en",) -> dict:
    try:
        ok = send_kanban_card_reopened(email = email, username = username, card_title = card_title, 
                                       project_name = project_name, language = language,)
        if not ok:
            raise smtplib.SMTPException("send_kanban_card_reopened returned False")
        logger.info(f"Kanban reopened email sent | card={card_title} | to={email[:4]}***")
        return {"success": True, "card": card_title}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_kanban_reopened_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_scrum_assigned_task",
             max_retries = _MAX_RETRIES, autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60,
             retry_jitter = True, acks_late = True,)
def send_scrum_assigned_task(self, email: str, username: str, issue_title: str, project_name: str,
                             language: str = "en",) -> dict:
    try:
        ok = send_scrum_issue_assigned(email = email, username = username, issue_title = issue_title, 
                                       project_name = project_name, language = language,)
        if not ok:
            raise smtplib.SMTPException("send_scrum_issue_assigned returned False")
        logger.info(f"Scrum assigned email sent | issue={issue_title} | to={email[:4]}***")
        return {"success": True, "issue": issue_title}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_scrum_assigned_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_scrum_sprint_started_task",
             max_retries = _MAX_RETRIES, autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, 
             retry_jitter = True, acks_late = True,)
def send_scrum_sprint_started_task(self, email: str, username: str, sprint_name: str, project_name: str,
                                   language: str = "en",) -> dict:
    try:
        ok = send_scrum_sprint_started(email = email, username = username, sprint_name = sprint_name,
                                       project_name = project_name, language = language,)
        if not ok:
            raise smtplib.SMTPException("send_scrum_sprint_started returned False")
        logger.info(f"Sprint started email sent | sprint={sprint_name} | to={email[:4]}***")
        return {"success": True, "sprint": sprint_name}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_scrum_sprint_started_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_scrum_sprint_completed_task",
             max_retries = _MAX_RETRIES, autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60,
             retry_jitter = True, acks_late = True,)
def send_scrum_sprint_completed_task(self, email: str, username: str, sprint_name: str, project_name: str, 
                                     language: str = "en",) -> dict:
    try:
        ok = send_scrum_sprint_completed(email = email, username = username, sprint_name = sprint_name, 
                                         project_name = project_name, language = language,)
        if not ok:
            raise smtplib.SMTPException("send_scrum_sprint_completed returned False")
        logger.info(f"Sprint completed email sent | sprint={sprint_name} | to={email[:4]}***")
        return {"success": True, "sprint": sprint_name}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_scrum_sprint_completed_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_workspace_invite_new_user_task",
             max_retries = _MAX_RETRIES, autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, 
             retry_jitter = True, acks_late = True,)
def send_workspace_invite_new_user_task(self, email: str, name: str, code: str, admin: str,) -> dict:
    try:
        ok = workspace_invitation_new_user(email = email, name = name, code = code, admin = admin,)
        if not ok:
            raise smtplib.SMTPException("workspace_invitation_new_user returned False")
        logger.info(f"Workspace new-user invite sent | workspace={name} | to={email[:4]}***")
        return {"success": True, "workspace": name}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_workspace_invite_new_user_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_project_member_added_task", max_retries = _MAX_RETRIES,
             autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, retry_jitter = True, acks_late = True,)
def send_project_member_added_task(self, email: str, username: str, project_name: str, workspace_id: int,
                                   role: str, language: str = "en",) -> dict:
    try:
        ok = send_project_member_added(email = email, username = username, project_name = project_name,
                                       workspace_id = workspace_id, role = role, language = language,)
        if not ok:
            raise smtplib.SMTPException("send_project_member_added returned False")
        logger.info(f"Project member added email sent | project={project_name} | to={email[:4]}***")
        return {"success": True, "project": project_name}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_project_member_added_task", email, exc)
        raise

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_project_member_removed_task",
             max_retries = _MAX_RETRIES, autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60,
             retry_jitter = True, acks_late = True,)
def send_project_member_removed_task(self, email: str, username: str, project_name: str, language: str = "en",) -> dict:
    try:
        ok = send_project_member_removed(email = email, username = username, project_name = project_name,
                                         language = language,)
        if not ok:
            raise smtplib.SMTPException("send_project_member_removed returned False")
        logger.info(f"Project member removed email sent | project={project_name} | to={email[:4]}***")
        return {"success": True, "project": project_name}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_project_member_removed_task", email, exc)
        raise

@celery_app.task(name = "app.utils.email.email_tasks.run_kanban_reminders_task", max_retries = 0, acks_late = True,
             ignore_result = False,)
def run_kanban_reminders_task() -> dict:
    db = SessionLocal()
    try:
        sent = send_kanban_deadline_reminders(db)
        logger.info(f"[Beat] Kanban reminders: sent {sent} email(s)")
        return {"sent": sent}
    except Exception as exc:
        logger.error(f"[Beat] Kanban reminder job failed: {exc}", exc_info=True)
        raise 
    finally:
        db.close()

@celery_app.task(name = "app.utils.email.email_tasks.run_scrum_reminders_task", max_retries = 0,  
             acks_late = True, ignore_result = False,)
def run_scrum_reminders_task() -> dict:
    db = SessionLocal()
    try:
        sent = send_scrum_scheduled_notifications(db)
        logger.info(f"[Beat] Scrum notifications: sent {sent} email(s)")
        return {"sent": sent}
    except Exception as exc:
        logger.error(f"[Beat] Scrum notification job failed: {exc}", exc_info=True)
        raise
    finally:
        db.close()

@celery_app.task(bind = True, name = "app.utils.email.email_tasks.send_scrum_reopened_task", max_retries = _MAX_RETRIES,
             autoretry_for = _RETRYABLE_EXCEPTIONS, retry_backoff = 60, retry_jitter = True, acks_late = True,)
def send_scrum_reopened_task(self, email: str, username: str, issue_title: str, project_name: str,
                             reopened_by: str, new_status: str, language: str = "en",) -> dict:
    try:
        ok = send_scrum_issue_reopened(email = email,
                                        username = username,
                                        issue_title = issue_title,
                                        project_name = project_name,
                                        reopened_by = reopened_by,
                                        new_status = new_status,
                                        language = language,)
        if not ok:
            raise smtplib.SMTPException("send_scrum_issue_reopened returned False")
        logger.info(f"Scrum reopened email sent | issue={issue_title} | to={email[:4]}***")
        return {"success": True, "issue": issue_title}
    except _RETRYABLE_EXCEPTIONS:
        raise
    except Exception as exc:
        _log_final_failure("send_scrum_reopened_task", email, exc)
        raise

@celery_app.task(name="app.utils.email.email_tasks.run_whiteboard_prune_task",max_retries=0, acks_late=True)
def run_whiteboard_prune_task() -> dict:
    db = SessionLocal()
    try:
        deleted = prune_old_history(db)
        return {"deleted": deleted}
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Whiteboard prune failed: %s", exc, exc_info=True)
        raise
    finally:
        db.close()