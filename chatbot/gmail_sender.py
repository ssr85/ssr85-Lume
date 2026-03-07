import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv

load_dotenv()

def send_gmail(to_email: str, subject: str, body: str, attachment_path: str = None) -> bool:
    """Sends an email using Gmail SMTP and App Password, optionally with an attachment."""
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
    
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
        except Exception as e:
            print(f"Attachment Error: {e}")
    
    try:
        # Using Port 465 for SSL
        print(f"Attempting to send email to {to_email} via {sender}...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_pass)
            server.sendmail(sender, to_email, msg.as_string())
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Gmail Send Error: {e}")
        return False
