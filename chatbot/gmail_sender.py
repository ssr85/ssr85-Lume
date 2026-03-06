import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_gmail(to_email: str, subject: str, body: str) -> bool:
    """Sends an email using Gmail SMTP and App Password."""
    sender = os.getenv("GMAIL_SENDER")
    app_pass = os.getenv("GMAIL_APP_PASS")
    
    if not sender or not app_pass:
        print("Gmail credentials missing in .env")
        return False
        
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    try:
        # Using Port 465 for SSL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_pass)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Gmail Send Error: {e}")
        return False
