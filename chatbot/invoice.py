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

def invoice_handler(message: str, session: dict, history: list = None):
    """Handles the invoice creation flow, including field collection and calculations."""
    from .intent import extract_fields
    
    extracted = extract_fields(message, "INVOICE", history=history)
    for key, val in extracted.items():
        if val and not session["collected_fields"].get(key):
            session["collected_fields"][key] = val
            
    # Auto-fill missing fields from database if client and project are known
    if session["collected_fields"].get("client_name") and session["collected_fields"].get("project_name"):
        client_id = db.find_client_by_name_and_email(session["collected_fields"]["client_name"])
        if client_id:
            client = db.get_client(client_id)
            proj_name = session["collected_fields"]["project_name"].lower()
            
            # 1. Search projects list
            matched_proj = next((p for p in client.get("projects", []) if p.get("title", "").lower() == proj_name), None)
            
            # 2. Fallback to proposals list
            if not matched_proj:
                matched_proj = next((p for p in client.get("proposals", []) if p.get("project_title", "").lower() == proj_name), None)
            
            if matched_proj:
                if not session["collected_fields"].get("work_items"):
                    session["collected_fields"]["work_items"] = matched_proj.get("deliverables", matched_proj.get("project_description", matched_proj.get("description", "Project Deliverables")))
                if not session["collected_fields"].get("rate"):
                    import re
                    budget_str = str(matched_proj.get("budget", ""))
                    nums = re.findall(r'\d+', budget_str.replace(",", ""))
                    if nums:
                        session["collected_fields"]["rate"] = float(nums[0])
                        
    # Required fields
    required = ["client_name", "project_name", "work_items", "rate"]
    missing = [f for f in required if not session["collected_fields"].get(f)]
    
    # Confirmation Keyword Detection (Direct Action)
    confirmation_keywords = ["proceed", "bill", "invoice it", "yes", "go ahead", "do it", "sure", "ok", "okay"]
    is_confirmed = any(kw in message.lower() for kw in confirmation_keywords)

    if missing:
        if not is_confirmed:
            field_labels = {
                "client_name": "client name",
                "project_name": "project title or name",
                "work_items": "detailed description of work",
                "rate": "hourly rate or flat fee"
            }
            return f"I'm ready to create that invoice. Could you provide the **{field_labels[missing[0]]}**?"

    # Client management
    client_name = session["collected_fields"]["client_name"]
    client_id = db.find_client_by_name_and_email(client_name)
    
    if not client_id and not session["collected_fields"].get("client_email"):
        return f"I see **{client_name}** is a new client. What's their email address so I can set them up?"

    if not client_id and session["collected_fields"].get("client_email"):
        client_id = db.get_or_create_client(
            name=client_name,
            email=session["collected_fields"]["client_email"]
        )
    elif client_id and session["collected_fields"].get("client_email"):
        # Update email if it was missing in DB
        client = db.get_client(client_id)
        if not client.get("email"):
            db.update_client_field(client_id, "email", session["collected_fields"]["client_email"])

    # Check if an UNPAID or PARTIAL invoice already exists for this project
    existing_invoice = None
    if client_id and session["collected_fields"].get("project_name"):
        client = db.get_client(client_id)
        proj_name = session["collected_fields"]["project_name"].lower()
        for inv in client.get("invoices", []):
            if inv.get("project_name", "").lower() == proj_name and inv.get("status") in ["UNPAID", "PARTIAL"]:
                existing_invoice = inv
                break
                
    if existing_invoice:
        # Avoid creating a duplicate. Regenerate the PDF for the existing invoice (to apply any new layouts) and return it.
        try:
            from documents.pdf_generator import generate_invoice_pdf
            pdf_path = existing_invoice.get("file_path", f"documents/invoices/{existing_invoice['invoice_number']}.pdf")
            invoice_for_pdf = {
                **existing_invoice,
                "client": db.get_client(client_id)
            }
            generate_invoice_pdf(invoice_for_pdf, pdf_path)
        except Exception as e:
            print(f"Error regenerating PDF: {e}")
            
        session.pop("current_intent", None)
        session.pop("collected_fields", None)
        return (f"### Invoice {existing_invoice['invoice_number']} retrieved\n\n"
                f"I found an existing pending invoice for **{client_name}** "
                f"totaling **${existing_invoice['grand_total']}** with **${existing_invoice['total_pending']}** remaining.\n\n"
                f"Preview: [**Open PDF Preview**](/{pdf_path})")

    # Calculation
    items = []
    # Assume simple extraction for now (one item or split by comma)
    if isinstance(session["collected_fields"]["work_items"], str):
        # Enhance the detailed description using the LLM
        raw_desc = session["collected_fields"]["work_items"]
        proj_name = session["collected_fields"].get("project_name", "")
        expand_prompt = (f"Write a professional, detailed 1-2 sentence description for this invoice line item. "
                         f"Project: {proj_name}. Notes: {raw_desc}. "
                         f"CRITICAL: Respond ONLY with the description text. Do NOT include any conversational filler, greetings, or next steps recommendations.")
        detailed_desc = call_llm(expand_prompt).strip()
        # Clean up stray quotes if the LLM adds them
        if detailed_desc.startswith('"') and detailed_desc.endswith('"'):
            detailed_desc = detailed_desc[1:-1]
            
        items = [{"description": detailed_desc, "hours": session["collected_fields"].get("hours", 1), "rate": session["collected_fields"]["rate"]}]
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
        "payments": [],
        "file_path": f"documents/invoices/{invoice_num}.pdf",
        "project_name": session["collected_fields"].get("project_name", "")
    }
    
    db.save_invoice(client_id, invoice_record)
    
    # Store Attachment Info for UI
    session["last_attachments"] = [{
        "name": f"Invoice_{invoice_num}.pdf",
        "url": f"/docs/invoices/{invoice_num}.pdf",
        "type": "pdf"
    }]
    # Generate PDF
    pdf_path = f"documents/invoices/{invoice_num}.pdf"
    
    invoice_for_pdf = {
        **invoice_record,
        "client": db.get_client(client_id)
    }
    
    from documents.pdf_generator import generate_invoice_pdf
    generate_invoice_pdf(invoice_for_pdf, pdf_path) 
    
    return (
        f"### Invoice {invoice_num} Generated\n\n"
        f"I've created the invoice for **{client_name}** totaling **${calc['grand_total']}**. You can preview it below before we proceed.\n\n"
        f"Preview: [**Open PDF Preview**](/docs/invoices/{invoice_num}.pdf)"
    )
