from .llm import call_llm
from storage import db
from datetime import datetime
from .gmail_sender import send_gmail

REMINDER_PROMPT = """
Write a professional payment reminder for {client_name}.
Tone: {tone} (gentle = warm/friendly, firm = direct/polite, urgent = assertive).

Details:
- Invoice: {invoice_num}
- Original Amount: ${total_amount}
- Amount Paid: ${total_paid}
- Pending Balance: ${total_pending}
- Due Date: {due_date}
- Days Overdue: {days_overdue}
- Freelancer: {freelancer_name}

Write the email as:
Subject: [subject]
Body: [body]
"""

def get_tone(due_date: str) -> str:
    """Selects tone based on days overdue."""
    due = datetime.strptime(due_date, "%Y-%m-%d")
    overdue = (datetime.now() - due).days
    if overdue <= 7: return "gentle"
    if overdue <= 21: return "firm"
    return "urgent"

def reminder_handler(message: str, session: dict):
    """Handles payment reminder generation and confirmation flow."""
    from .intent import extract_fields
    msg_low = message.lower().strip()
    
    # Check if we are in a confirmation state
    if "draft_reminder" in session:
        if any(kw in msg_low for kw in ["yes", "proceed", "go ahead", "send it", "do it"]):
            draft = session["draft_reminder"]
            target_email = session["target_client_email"]
            
            # Extract subject and body from draft
            # Draft format is expected to be "Subject: [subject]\nBody: [body]"
            subject = "Payment Reminder"
            body = draft
            if "Subject:" in draft and "Body:" in draft:
                parts = draft.split("Body:", 1)
                subject_part = parts[0].replace("Subject:", "").strip()
                body_part = parts[1].strip()
                subject = subject_part
                body = body_part

            success = send_gmail(target_email, subject, body)
            
            # Clear session state
            del session["draft_reminder"]
            del session["target_client_email"]
            
            if success:
                return f"✅ **Reminder sent successfully** to {target_email}."
            else:
                return "❌ **Failed to send email.** Please check your Gmail App Password in `.env` or system logs."
        
        elif any(kw in msg_low for kw in ["no", "stop", "cancel", "don't"]):
            del session["draft_reminder"]
            del session["target_client_email"]
            return "Reminder cancelled. What else can I help you with?"

    extracted = extract_fields(message, "REMINDER")
    client_name = extracted.get("client_name")
    
    if not client_name:
        # Fallback: check if the message itself is a name or contains a name from history
        return "Which client should I send a reminder to?"

    # Find the unpaid invoice for this client
    # (Simplified: assumes latest unpaid invoice)
    db_data = db.get_raw_database()
    client_id = db.find_client_by_name_and_email(client_name)
    if not client_id:
        return f"I couldn't find a client named '{client_name}'."
        
    client = db.get_client(client_id)
    unpaid_invoices = [inv for inv in client.get("invoices", []) if inv["status"] != "PAID"]
    
    if not unpaid_invoices:
        return f"Good news! **{client_name}** has no unpaid invoices."
        
    invoice = unpaid_invoices[0] # Take the first one for now
    tone = get_tone(invoice["due_date"])
    
    prompt = REMINDER_PROMPT.format(
        client_name=client_name,
        tone=tone,
        invoice_num=invoice["invoice_number"],
        total_amount=invoice["grand_total"],
        total_paid=invoice["total_paid"],
        total_pending=invoice["total_pending"],
        due_date=invoice["due_date"],
        days_overdue=(datetime.now() - datetime.strptime(invoice["due_date"], "%Y-%m-%d")).days,
        freelancer_name=os.getenv("FREELANCER_NAME", "your assistant")
    )
    
    draft = call_llm(prompt)
    session["draft_reminder"] = draft
    session["target_client_email"] = client["email"]
    
    return (
        f"### Reminder Draft ({tone.capitalize()} Tone)\n\n{draft}\n\n"
        f"**Please review the email draft above.** Shall I send this to {client['email']}? (Reply 'Yes' to confirm and send)"
    )
