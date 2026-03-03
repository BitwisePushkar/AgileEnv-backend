from app.utils.email.core import SUPPORTED_LANGUAGES
from app.utils.email.otp import send_otp_email
from app.utils.email.workspace import (workspace_invitation,workspace_welcome,workspace_invitation_new_user)
from app.utils.email.project import (send_project_member_added,send_project_member_removed,)
from app.utils.email.kanban import (send_kanban_card_assigned,send_kanban_card_completed,send_kanban_deadline_72h,
                                    send_kanban_deadline_24h,send_kanban_deadline_2h,send_kanban_overdue_assignee,
                                    send_kanban_overdue_creator,)

__all__ = [
    "SUPPORTED_LANGUAGES",
    "send_otp_email",
    "workspace_invitation",
    "workspace_welcome",
    "workspace_invitation_new_user",
    "send_project_member_added",
    "send_project_member_removed",
    "send_kanban_card_assigned",
    "send_kanban_card_completed",
    "send_kanban_deadline_72h",
    "send_kanban_deadline_24h",
    "send_kanban_deadline_2h",
    "send_kanban_overdue_assignee",
    "send_kanban_overdue_creator",
]