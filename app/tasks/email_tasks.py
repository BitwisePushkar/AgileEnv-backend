from app.celery_app import celery_app
from app.config import Settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart




settings = Settings()

@celery_app.task(name = "send_otp_email")
def send_otp_email(email :str,otp_code:str,purpose:str):
    """
    Send OTP email to user
    """
    try:

        subject = "Your OTP Code"
        
        if purpose == "registration":
            body = f"""
            <h2>Welcome to Alige!</h2>
            <p>Your OTP code is: <strong>{otp_code}</strong></p>
            <p>This code will expire in 5 minutes.</p>
            """
        else: 
            body = f"""
            <h2>Password Reset Request</h2>
            <p>Your OTP code is: <strong>{otp_code}</strong></p>
            <p>This code will expire in 5 minutes.</p>
            """

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM
        message["To"] = email

        html_part = MIMEText(body, "html")
        message.attach(html_part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, email, message.as_string())
        
        return {"status": "success", "email": email}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
