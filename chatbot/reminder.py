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
    
    extracted = extract_fields(message, "REMINDER")
    client_name = extracted.get("client_name")
    
    if not client_name:
        return "Which client should I send a reminder to?"

    # Find the unpaid invoice for this client
    # (Simplified: assumes latest unpaid invoice)
    db_data = db.load_db()
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
        f"**Shall I send this to {client['email']}?** (Reply 'Yes' to send)"
    )
