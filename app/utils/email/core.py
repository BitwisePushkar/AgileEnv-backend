import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.utils.settings import settings

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"en", "hi", "fr", "zh"}

def _send_email(to_email: str, subject: str, html: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email[:4]}*** | Subject: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check SMTP_USER and SMTP_PASSWORD in .env")
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"SMTP rejected recipient {to_email[:4]}*** — address may be invalid")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {to_email[:4]}***: {e}")
        return False
    except TimeoutError:
        logger.error("SMTP connection timed out — check SMTP_HOST and SMTP_PORT in .env")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email[:4]}***: {e}")
        return False

def _get_template(registry: dict, language: str):
    return registry.get(language) or registry["en"]