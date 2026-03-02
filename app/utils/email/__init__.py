from app.utils.email.core import SUPPORTED_LANGUAGES
from app.utils.email.otp import send_otp_email
from app.utils.email.workspace import (workspace_invitation,workspace_welcome,workspace_invitation_new_user)

__all__ = [
    "SUPPORTED_LANGUAGES",
    "send_otp_email",
    "workspace_invitation",
    "workspace_welcome",
    "workspace_invitation_new_user",
]