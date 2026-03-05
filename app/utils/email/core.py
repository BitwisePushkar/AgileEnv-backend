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
        msg["From"] = f"Agile App <{settings.EMAIL_HOST_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        if settings.EMAIL_USE_SSL:
            with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15) as server:
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.sendmail(settings.EMAIL_HOST_USER, to_email, msg.as_string())

        elif settings.EMAIL_USE_TLS:
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.sendmail(settings.EMAIL_HOST_USER, to_email, msg.as_string())

        else:
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15) as server:
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.sendmail(settings.EMAIL_HOST_USER, to_email, msg.as_string())

        logger.info(f"Email sent | to={to_email[:4]}*** | subject={subject!r}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"SMTP rejected recipient {to_email[:4]}*** — address may be invalid or blocked")
        return False
    except smtplib.SMTPConnectError:
        logger.error(f"SMTP connection failed — check EMAIL_HOST ({settings.EMAIL_HOST}) and EMAIL_PORT ({settings.EMAIL_PORT}) in .env")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {to_email[:4]}***: {e}")
        return False
    except TimeoutError:
        logger.error(f"SMTP connection timed out — EMAIL_HOST={settings.EMAIL_HOST} EMAIL_PORT={settings.EMAIL_PORT}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email[:4]}***: {e}")
        return False

def _get_template(registry: dict, language: str):
    return registry.get(language) or registry["en"]