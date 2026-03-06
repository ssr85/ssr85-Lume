# Gmail Integration Setup

## Overview

Gmail integration is **mandatory** for this project. The system sends payment reminder emails directly from the freelancer's Gmail account using Python's `smtplib` library with a **Gmail App Password**. The main Gmail account password must never appear in any code or config file.

---

## Step-by-Step Setup

### Step 1 -- Enable 2-Step Verification

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Navigate to **Security**
3. Under "How you sign in to Google", enable **2-Step Verification**
4. Follow the prompts to complete setup

### Step 2 -- Generate an App Password

1. Go to **Google Account > Security > App Passwords**
   (2-Step Verification must be enabled to see this option)
2. Under "Select app", choose **Mail**
3. Under "Select device", choose **Other (Custom name)**
4. Enter a name like `FreelancerBot`
5. Click **Generate**
6. Copy the 16-character password shown (e.g. `abcd efgh ijkl mnop`)

> You will only see this password once. Store it immediately.

### Step 3 -- Store Credentials in `.env`

Create a `.env` file in the project root:

```env
GMAIL_SENDER=yourname@gmail.com
GMAIL_APP_PASS=abcdefghijklmnop
FREELANCER_NAME="Your Name"
```

> **Never commit `.env` to Git.** Add it to `.gitignore`:

```
# .gitignore
.env
```

### Step 4 -- Load Credentials in Code

```python
import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS")
```

---

## Sending Email with smtplib

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_reminder_email(to_email: str, subject: str, body: str) -> bool:
    sender = os.getenv("GMAIL_SENDER")
    app_pass = os.getenv("GMAIL_APP_PASS")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_pass)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Check GMAIL_APP_PASS in .env")
        return False
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
```

---

## Email Structure

| Field | Source |
|---|---|
| **From** | `GMAIL_SENDER` from `.env` |
| **To** | Client's email address from storage |
| **Subject** | Auto-generated based on invoice details |
| **Body** | AI-generated reminder text (tone-adjusted) |

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `SMTPAuthenticationError` | Wrong App Password or 2FA not enabled | Re-generate App Password; ensure 2FA is on |
| `Connection refused` | Port blocked or wrong SMTP config | Use `smtp.gmail.com` port `465` (SSL) |
| Email not received | App password has spaces | Remove spaces from the 16-char App Password in `.env` |
| "Less secure app access" error | Using main password instead of App Password | Switch to App Password only |

---

## Security Rules

- Store credentials only in `.env`
- Load with `python-dotenv`
- Add `.env` to `.gitignore`
- Never hardcode credentials in any `.py` file
- Never print or log the App Password
- Never commit `.env` to version control
