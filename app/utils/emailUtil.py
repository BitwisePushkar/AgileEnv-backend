from functools import lru_cache
from app import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

@lru_cache()
def get_settings():
    return config.Settings()

settings = get_settings()
API_KEY = settings.API_KEY
FROM_EMAIL = settings.FROM_EMAIL

def get_registration_html(otp:str,username:str)->str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 30px; border-radius: 10px;">
            <h2 style="color: #4CAF50;">Welcome to Agile App! 🎉</h2>
            <p>Hi <strong>{username}</strong>,</p>
            <p>Your OTP code for registration:</p>
            <div style="background: white; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                <h1 style="color: #4CAF50; letter-spacing: 5px;">{otp}</h1>
            </div>
            <p><strong>Valid for 10 minutes</strong></p>
            <p>If you didn't request this, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

def get_password_reset_html(otp: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff3e0; padding: 30px; border-radius: 10px;">
            <h2 style="color: #FF5722;">Password Reset Request 🔐</h2>
            <p>Your OTP code for password reset:</p>
            <div style="background: white; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                <h1 style="color: #FF5722; letter-spacing: 5px;">{otp}</h1>
            </div>
            <p><strong>Valid for 10 minutes</strong></p>
            <p style="color: #d32f2f;">⚠️ Never share this OTP with anyone!</p>
            <p>If you didn't request this, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

def send_otp_email(email: str, otp: str, purpose: str, username: str = "User"):
    try:
        if purpose == "registration":
            subject = "Your Registration OTP"
            html = get_registration_html(otp, username)
        elif purpose == "password_reset":
            subject = "Your Password Reset OTP"
            html = get_password_reset_html(otp)
        else:
            return False
        message = Mail(from_email=FROM_EMAIL,to_emails=email,subject=subject,html_content=html)
        sg = SendGridAPIClient(API_KEY)
        response = sg.send(message)
        print(f"Email sent to {email} - Status: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False