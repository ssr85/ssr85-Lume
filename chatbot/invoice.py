import os
from .llm import call_llm
from storage import db
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def calculate_invoice(items: list, tax_percent: float = 0) -> dict:
    """Performs invoice calculations including subtotals and tax."""
    processed_items = []
    total_before_tax = 0
    
    for item in items:
        # Expected keys: description, hours, rate
        hours = float(item.get("hours", 0))
        rate = float(item.get("rate", 0))
        subtotal = round(hours * rate, 2)
        processed_items.append({
            "description": item.get("description", "Work item"),
            "hours": hours,
            "rate": rate,
            "subtotal": subtotal
        })
        total_before_tax += subtotal
        
    tax_amount = round(total_before_tax * (tax_percent / 100), 2)
    grand_total = round(total_before_tax + tax_amount, 2)
    
    return {
        "items": processed_items,
        "subtotal": total_before_tax,
        "tax_percent": tax_percent,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
        "total_paid": 0,
        "total_pending": grand_total
    }

def invoice_handler(message: str, session: dict):
    """Handles the invoice creation flow, including field collection and calculations."""
    from .intent import extract_fields
    
    extracted = extract_fields(message, "INVOICE")
    for key, val in extracted.items():
        if val and not session["collected_fields"].get(key):
            session["collected_fields"][key] = val
            
    # Required fields
    required = ["client_name", "work_items", "rate"]
    missing = [f for f in required if not session["collected_fields"].get(f)]
    
    if missing:
        field_labels = {
            "client_name": "client name",
            "work_items": "description of work",
            "rate": "hourly rate"
        }
        return f"I'm ready to create that invoice. Could you provide the **{field_labels[missing[0]]}**?"

    # Client management
    client_name = session["collected_fields"]["client_name"]
    client_id = db.find_client_by_name_and_email(client_name)
    
    if not client_id and not session["collected_fields"].get("client_email"):
        return f"I see **{client_name}** is a new client. What's their email address so I can set them up?"

    if not client_id:
        client_id = db.get_or_create_client(
            name=client_name,
            email=session["collected_fields"]["client_email"]
        )

    # Calculation
    items = []
    # Assume simple extraction for now (one item or split by comma)
    if isinstance(session["collected_fields"]["work_items"], str):
        items = [{"description": session["collected_fields"]["work_items"], "hours": session["collected_fields"].get("hours", 1), "rate": session["collected_fields"]["rate"]}]
    else:
        items = session["collected_fields"]["work_items"]
        
    calc = calculate_invoice(items, tax_percent=float(session["collected_fields"].get("tax", 0)))
    
    invoice_num = db.get_next_invoice_number()
    due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    invoice_record = {
        "invoice_number": invoice_num,
        "invoice_date": datetime.now().strftime("%Y-%m-%d"),
        "due_date": due_date,
        **calc,
        "status": "UNPAID",
        "reminders_sent": [],
        "payments": []
    }
    
    db.save_invoice(client_id, invoice_record)
    
    # Store Attachment Info for UI
    session["last_attachments"] = [{
        "name": f"Invoice_{invoice_num}.pdf",
        "url": f"/docs/invoices/{invoice_num}.pdf",
        "type": "pdf"
    }]
    
    # Generate PDF (Staging)
    pdf_path = f"documents/invoices/{invoice_num}.pdf"
    # generate_invoice_pdf(invoice_record, pdf_path) # Would call pdf_generator
    
    return (
        f"### Invoice Draft {invoice_num} (For Your Review)\n\n"
        f"**Client:** {client_name}\n"
        f"**Amount Due:** ${calc['grand_total']}\n"
        f"**Due Date:** {due_date}\n\n"
        "--- \n"
        "**Please review the generated invoice.**\n\n"
        f"Preview: [**Open PDF Preview**](/docs/invoices/{invoice_num}.pdf)"
    )
