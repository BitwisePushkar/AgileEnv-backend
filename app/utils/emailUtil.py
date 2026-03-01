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
        logger.info(f"Email sent via SMTP2GO to {to_email[:4]}*** | Subject: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP2GO authentication failed — check SMTP_USER and SMTP_PASSWORD in .env")
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"SMTP2GO rejected recipient {to_email[:4]}*** — address may be invalid")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP2GO error sending to {to_email[:4]}***: {e}")
        return False
    except TimeoutError:
        logger.error("SMTP2GO connection timed out — check SMTP_HOST and SMTP_PORT in .env")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email[:4]}***: {e}")
        return False

def _get_template(registry: dict, language: str):
    return registry.get(language) or registry["en"]

def _registration_html_en(otp: str, username: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #4CAF50;">Welcome to Agile App! 🎉</h2>
            <p>Hi <strong>{username}</strong>,</p>
            <p>Thank you for registering. Use the OTP below to verify your email address:</p>
            <div style="background: #f9f9f9; padding: 20px; text-align: center; border-radius: 8px; margin: 24px 0; border: 1px solid #e0e0e0;">
                <p style="margin: 0 0 8px 0; color: #666; font-size: 14px;">Your verification code</p>
                <h1 style="color: #4CAF50; letter-spacing: 8px; margin: 0; font-size: 36px;">{otp}</h1>
            </div>
            <p><strong>⏱ Valid for 10 minutes only.</strong></p>
            <p style="color: #888; font-size: 13px;">If you did not create an account, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

_REGISTRATION_TEMPLATES = {
    "en": _registration_html_en,
}

def _password_reset_html_en(otp: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #FF5722;">Password Reset Request 🔐</h2>
            <p>We received a request to reset your Agile App password.</p>
            <p>Use the OTP below to proceed:</p>
            <div style="background: #fff3e0; padding: 20px; text-align: center; border-radius: 8px; margin: 24px 0; border: 1px solid #ffe0cc;">
                <p style="margin: 0 0 8px 0; color: #888; font-size: 14px;">Your reset code</p>
                <h1 style="color: #FF5722; letter-spacing: 8px; margin: 0; font-size: 36px;">{otp}</h1>
            </div>
            <p><strong>⏱ Valid for 10 minutes only.</strong></p>
            <p style="color: #d32f2f; font-size: 13px;">⚠️ Never share this OTP with anyone, including Agile App support.</p>
            <p style="color: #888; font-size: 13px;">If you did not request a password reset, please ignore this email. Your account is safe.</p>
        </div>
    </body>
    </html>
    """

def _password_reset_html_hi(otp: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #FF5722;">पासवर्ड रीसेट अनुरोध 🔐</h2>
            <p>हमें आपके Agile App पासवर्ड को रीसेट करने का अनुरोध मिला है।</p>
            <p>आगे बढ़ने के लिए नीचे दिए गए OTP का उपयोग करें:</p>
            <div style="background: #fff3e0; padding: 20px; text-align: center; border-radius: 8px; margin: 24px 0; border: 1px solid #ffe0cc;">
                <p style="margin: 0 0 8px 0; color: #888; font-size: 14px;">आपका रीसेट कोड</p>
                <h1 style="color: #FF5722; letter-spacing: 8px; margin: 0; font-size: 36px;">{otp}</h1>
            </div>
            <p><strong>⏱ यह कोड केवल 10 मिनट के लिए वैध है।</strong></p>
            <p style="color: #d32f2f; font-size: 13px;">⚠️ यह OTP किसी के साथ भी साझा न करें, यहाँ तक कि Agile App सहायता से भी नहीं।</p>
            <p style="color: #888; font-size: 13px;">यदि आपने पासवर्ड रीसेट का अनुरोध नहीं किया है, तो इस ईमेल को अनदेखा करें। आपका खाता सुरक्षित है।</p>
        </div>
    </body>
    </html>
    """

def _password_reset_html_fr(otp: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #FF5722;">Demande de réinitialisation du mot de passe 🔐</h2>
            <p>Nous avons reçu une demande de réinitialisation de votre mot de passe Agile App.</p>
            <p>Utilisez le code OTP ci-dessous pour continuer :</p>
            <div style="background: #fff3e0; padding: 20px; text-align: center; border-radius: 8px; margin: 24px 0; border: 1px solid #ffe0cc;">
                <p style="margin: 0 0 8px 0; color: #888; font-size: 14px;">Votre code de réinitialisation</p>
                <h1 style="color: #FF5722; letter-spacing: 8px; margin: 0; font-size: 36px;">{otp}</h1>
            </div>
            <p><strong>⏱ Valable 10 minutes seulement.</strong></p>
            <p style="color: #d32f2f; font-size: 13px;">⚠️ Ne partagez jamais ce code avec qui que ce soit, y compris le support Agile App.</p>
            <p style="color: #888; font-size: 13px;">Si vous n'avez pas demandé de réinitialisation, ignorez cet e-mail. Votre compte est en sécurité.</p>
        </div>
    </body>
    </html>
    """

def _password_reset_html_zh(otp: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #FF5722;">密码重置请求 🔐</h2>
            <p>我们收到了重置您的 Agile App 密码的请求。</p>
            <p>请使用以下验证码继续操作：</p>
            <div style="background: #fff3e0; padding: 20px; text-align: center; border-radius: 8px; margin: 24px 0; border: 1px solid #ffe0cc;">
                <p style="margin: 0 0 8px 0; color: #888; font-size: 14px;">您的重置验证码</p>
                <h1 style="color: #FF5722; letter-spacing: 8px; margin: 0; font-size: 36px;">{otp}</h1>
            </div>
            <p><strong>⏱ 验证码仅在 10 分钟内有效。</strong></p>
            <p style="color: #d32f2f; font-size: 13px;">⚠️ 请勿将此验证码分享给任何人，包括 Agile App 客服。</p>
            <p style="color: #888; font-size: 13px;">如果您没有申请重置密码，请忽略此邮件。您的账户是安全的。</p>
        </div>
    </body>
    </html>
    """

_PASSWORD_RESET_TEMPLATES = {
    "en": _password_reset_html_en,
    "hi": _password_reset_html_hi,
    "fr": _password_reset_html_fr,
    "zh": _password_reset_html_zh,
}

def _workspace_invite_html_en(name: str, code: str, admin: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #4a5568;">You've been invited! 🎊</h2>
            <p><strong>{admin}</strong> has invited you to join the workspace:</p>
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 24px 0; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0 0 12px 0; color: #2d3748;">{name}</h3>
                <p style="margin: 0; color: #555;">Use this security code to join:</p>
                <div style="margin-top: 12px; text-align: center;">
                    <code style="background: #edf2f7; padding: 10px 20px; border-radius: 6px; font-size: 20px; letter-spacing: 4px; color: #2d3748; font-weight: bold;">{code}</code>
                </div>
            </div>
            <p style="color: #555;">Open Agile App, go to <strong>Join Workspace</strong>, enter the workspace ID and the code above.</p>
            <p style="color: #888; font-size: 13px;">If you were not expecting this invitation, you can safely ignore this email.</p>
        </div>
    </body>
    </html>
    """

def _workspace_invite_html_hi(name: str, code: str, admin: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #4a5568;">आपको आमंत्रित किया गया है! 🎊</h2>
            <p><strong>{admin}</strong> ने आपको इस वर्कस्पेस में शामिल होने के लिए आमंत्रित किया है:</p>
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 24px 0; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0 0 12px 0; color: #2d3748;">{name}</h3>
                <p style="margin: 0; color: #555;">जुड़ने के लिए इस सुरक्षा कोड का उपयोग करें:</p>
                <div style="margin-top: 12px; text-align: center;">
                    <code style="background: #edf2f7; padding: 10px 20px; border-radius: 6px; font-size: 20px; letter-spacing: 4px; color: #2d3748; font-weight: bold;">{code}</code>
                </div>
            </div>
            <p style="color: #555;">Agile App खोलें, <strong>Join Workspace</strong> पर जाएं, वर्कस्पेस ID और ऊपर दिया गया कोड दर्ज करें।</p>
            <p style="color: #888; font-size: 13px;">यदि आप इस आमंत्रण की उम्मीद नहीं कर रहे थे, तो इस ईमेल को अनदेखा करें।</p>
        </div>
    </body>
    </html>
    """

def _workspace_invite_html_fr(name: str, code: str, admin: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #4a5568;">Vous avez été invité(e) ! 🎊</h2>
            <p><strong>{admin}</strong> vous invite à rejoindre l'espace de travail :</p>
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 24px 0; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0 0 12px 0; color: #2d3748;">{name}</h3>
                <p style="margin: 0; color: #555;">Utilisez ce code de sécurité pour rejoindre :</p>
                <div style="margin-top: 12px; text-align: center;">
                    <code style="background: #edf2f7; padding: 10px 20px; border-radius: 6px; font-size: 20px; letter-spacing: 4px; color: #2d3748; font-weight: bold;">{code}</code>
                </div>
            </div>
            <p style="color: #555;">Ouvrez Agile App, allez dans <strong>Rejoindre un espace</strong>, entrez l'ID de l'espace et le code ci-dessus.</p>
            <p style="color: #888; font-size: 13px;">Si vous n'attendiez pas cette invitation, vous pouvez ignorer cet e-mail.</p>
        </div>
    </body>
    </html>
    """

def _workspace_invite_html_zh(name: str, code: str, admin: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #4a5568;">您收到了邀请！🎊</h2>
            <p><strong>{admin}</strong> 邀请您加入工作空间：</p>
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 24px 0; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0 0 12px 0; color: #2d3748;">{name}</h3>
                <p style="margin: 0; color: #555;">请使用以下安全码加入：</p>
                <div style="margin-top: 12px; text-align: center;">
                    <code style="background: #edf2f7; padding: 10px 20px; border-radius: 6px; font-size: 20px; letter-spacing: 4px; color: #2d3748; font-weight: bold;">{code}</code>
                </div>
            </div>
            <p style="color: #555;">打开 Agile App，进入 <strong>加入工作空间</strong>，输入工作空间 ID 和上方的安全码。</p>
            <p style="color: #888; font-size: 13px;">如果您未预期收到此邀请，可以安全地忽略此邮件。</p>
        </div>
    </body>
    </html>
    """

_WORKSPACE_INVITE_TEMPLATES = {
    "en": _workspace_invite_html_en,
    "hi": _workspace_invite_html_hi,
    "fr": _workspace_invite_html_fr,
    "zh": _workspace_invite_html_zh,
}

def send_otp_email(email: str,otp: str,purpose: str,username: str = "User",language: str = "en",) -> bool:
    if purpose == "registration":
        subject = "Verify your Agile App account"
        html = _registration_html_en(otp, username)

    elif purpose == "password_reset":
        subjects = {
            "en": "Your Agile App password reset code",
            "hi": "आपका Agile App पासवर्ड रीसेट कोड",
            "fr": "Votre code de réinitialisation Agile App",
            "zh": "您的 Agile App 密码重置验证码",
        }
        subject = subjects.get(language) or subjects["en"]
        html = _get_template(_PASSWORD_RESET_TEMPLATES, language)(otp)

    else:
        logger.warning(f"Unknown email purpose '{purpose}' for {email[:4]}***")
        return False

    return _send_email(email, subject, html)

def workspace_invitation(email: str,name: str,code: str,admin: str,language: str = "en",) -> bool:
    subjects = {
        "en": f"You're invited to join {name} on Agile App",
        "hi": f"Agile App पर {name} में शामिल होने का आमंत्रण",
        "fr": f"Invitation à rejoindre {name} sur Agile App",
        "zh": f"邀请您加入 Agile App 上的 {name}",
    }
    subject = subjects.get(language) or subjects["en"]
    html = _get_template(_WORKSPACE_INVITE_TEMPLATES, language)(name, code, admin)
    return _send_email(email, subject, html)