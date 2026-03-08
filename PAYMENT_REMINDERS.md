# Payment Reminders

## Overview

When the intent is `REMINDER`, the chatbot generates a professional payment reminder and sends it directly to the client via Gmail. The tone is automatically adjusted based on how many days overdue the invoice is.

---

## Trigger Examples

```
"Send a reminder to Acme Corp for invoice #1042"
"Generate a follow-up for the unpaid invoice from last month"
"Write a second reminder for the website project -- they're two weeks late"
"PeakForm still hasn't paid. Invoice is 10 days overdue."
```

---

## Tone Levels & Memory Influence

| Overdue Duration | Tone | Character |
|---|---|---|
| **1-7 days** | Gentle | Friendly reminder, assumes the client forgot. Warm and non-pressuring. |
| **8-21 days** | Firm | Polite but direct. Makes clear the payment is overdue and expected promptly. |
| **22+ days** | Urgent | Professional but firm. May reference consequences such as work pause or late fees. |

> [!IMPORTANT]
> Specific **Tone Preferences** or **Archived Rules** stored in the client's **Memory** (e.g., "Sarah appreciates extra-gentle reminders regardless of delay") will override these default tone levels.

### Tone Detection Logic

```python
def get_tone(due_date: str) -> str:
    from datetime import date
    days_overdue = (date.today() - date.fromisoformat(due_date)).days
    if days_overdue <= 7:
        return "gentle"
    elif days_overdue <= 21:
        return "firm"
    else:
        return "urgent"
```

---

## Reminder Generation Prompt

```python
REMINDER_PROMPT = """
You are a professional payment reminder writer for a freelancer.
Write a payment reminder email using the details below.

Tone instructions:
- gentle: Assume the client forgot. Be warm, friendly, and understanding. No pressure.
- firm: Be polite but direct. The payment is clearly overdue. Expect prompt action.
- urgent: Be professional but assertive. Reference consequences if appropriate.

Details:
- Client Name: {client_name}
- Invoice Number: {invoice_number}
- Total Invoice Amount: {total_amount}
- Total Paid So Far: {total_paid}
- Current Pending Balance: {total_pending}
- Original Due Date: {due_date}
- Days Overdue: {days_overdue}
- Freelancer Name: {freelancer_name}
- Freelancer Contact: {freelancer_contact}
- Payment Details: {payment_details}
- Tone: {tone}

Write:
Subject: [email subject line]
Body: [full email body]

Use the client's name in the greeting. Be concise. Do not use placeholder text.
"""
```

---

## Send Flow

```
Step 1: Freelancer requests a reminder
Step 2: System looks up the invoice and client email from storage
Step 3: System calculates days overdue and selects tone
Step 4: LLM generates the reminder email (subject + body)
Step 5: Draft is displayed in chat for the freelancer to review
Step 6: Bot asks: "Shall I send this to [client_email]?"
Step 7: Freelancer confirms: "Yes, send it"
Step 8: Gmail sends the email via smtplib
Step 9: System logs the reminder (timestamp, tone used, recipient)
Step 10: Bot confirms: "Reminder sent to [client_email] at [time]"
```

---

## What the Reminder Must Include

- Client name and personalised greeting
- Invoice number and the outstanding amount
- Original due date and exact number of days overdue
- Polite but tone-appropriate request for payment
- Payment details or reference to the original invoice
- Freelancer's name and contact information

---

## Reminder Logging

Every sent reminder is logged in the client's invoice record:

```json
"reminders_sent": [
  {
    "sent_at": "2026-03-06T10:30:00",
    "tone": "firm",
    "recipient": "contact@peakform.com",
    "subject": "Follow-Up on Invoice #INV-1043",
    "days_overdue_at_send": 10
  }
]
```

---

## Example Reminder (Firm Tone, 10 Days Overdue)

**Subject:** Follow-Up on Invoice #INV-1043

> Hi PeakForm Team,
>
> I hope you're doing well. I'm writing to follow up on Invoice #INV-1043 for $1,800, which was due on 24 February 2026. The invoice is now 10 days past due.
>
> Could you please arrange payment at your earliest convenience? If you have any questions about the invoice, I'm happy to help.
>
> Payment can be made via [payment details].
>
> Thank you for your attention to this.
>
> Best regards,
> [Freelancer Name]
> [Email] - [Phone]
