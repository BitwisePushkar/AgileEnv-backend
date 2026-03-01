from app.utils.email.core import _send_email, _get_template

def _registration_html_en(otp: str, username: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px;
                    border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #4CAF50;">Welcome to Agile App! 🎉</h2>
            <p>Hi <strong>{username}</strong>,</p>
            <p>Thank you for registering. Use the OTP below to verify your email address:</p>
            <div style="background: #f9f9f9; padding: 20px; text-align: center;
                        border-radius: 8px; margin: 24px 0; border: 1px solid #e0e0e0;">
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
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px;
                    border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #FF5722;">Password Reset Request 🔐</h2>
            <p>We received a request to reset your Agile App password.</p>
            <p>Use the OTP below to proceed:</p>
            <div style="background: #fff3e0; padding: 20px; text-align: center;
                        border-radius: 8px; margin: 24px 0; border: 1px solid #ffe0cc;">
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
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px;
                    border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #FF5722;">पासवर्ड रीसेट अनुरोध 🔐</h2>
            <p>हमें आपके Agile App पासवर्ड को रीसेट करने का अनुरोध मिला है।</p>
            <p>आगे बढ़ने के लिए नीचे दिए गए OTP का उपयोग करें:</p>
            <div style="background: #fff3e0; padding: 20px; text-align: center;
                        border-radius: 8px; margin: 24px 0; border: 1px solid #ffe0cc;">
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
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px;
                    border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #FF5722;">Demande de réinitialisation du mot de passe 🔐</h2>
            <p>Nous avons reçu une demande de réinitialisation de votre mot de passe Agile App.</p>
            <p>Utilisez le code OTP ci-dessous pour continuer :</p>
            <div style="background: #fff3e0; padding: 20px; text-align: center;
                        border-radius: 8px; margin: 24px 0; border: 1px solid #ffe0cc;">
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
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px;
                    border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #FF5722;">密码重置请求 🔐</h2>
            <p>我们收到了重置您的 Agile App 密码的请求。</p>
            <p>请使用以下验证码继续操作：</p>
            <div style="background: #fff3e0; padding: 20px; text-align: center;
                        border-radius: 8px; margin: 24px 0; border: 1px solid #ffe0cc;">
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

_PASSWORD_RESET_SUBJECTS = {
    "en": "Your Agile App password reset code",
    "hi": "आपका Agile App पासवर्ड रीसेट कोड",
    "fr": "Votre code de réinitialisation Agile App",
    "zh": "您的 Agile App 密码重置验证码",
}

def send_otp_email(email: str,otp: str,purpose: str,username: str = "User",language: str = "en",) -> bool:
    if purpose == "registration":
        subject = "Verify your Agile App account"
        html = _registration_html_en(otp, username)
    elif purpose == "password_reset":
        subject = _PASSWORD_RESET_SUBJECTS.get(language) or _PASSWORD_RESET_SUBJECTS["en"]
        html = _get_template(_PASSWORD_RESET_TEMPLATES, language)(otp)
    else:
        import logging
        logging.getLogger(__name__).warning(f"send_otp_email: unknown purpose '{purpose}' for {email[:4]}***")
        return False
    return _send_email(email, subject, html)