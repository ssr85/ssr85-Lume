import json
import os
from datetime import datetime

DATA_FILE = "storage/data.json"

def load_db() -> dict:
    """Loads the database from JSON. Returns a fresh structure if file missing."""
    if not os.path.exists(DATA_FILE):
        return {
            "last_invoice_number": 1000,
            "last_client_id": 1000,
            "clients": {}
        }
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"last_invoice_number": 1000, "last_client_id": 1000, "clients": {}}

def save_db(data: dict):
    """Saves the database to JSON with atomic intent."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_next_client_id() -> str:
    """Generates an incremental ClientID."""
    db = load_db()
    new_id_num = db.get("last_client_id", 1000) + 1
    db["last_client_id"] = new_id_num
    save_db(db)
    return f"CLT-{new_id_num}"

def find_client_by_name_and_email(name: str, email: str = None) -> str:
    """Searches for a client by name and optionally email. Returns ClientID if found."""
    db = load_db()
    for cid, client in db["clients"].items():
        if client["name"].lower() == name.lower():
            if email:
                if client.get("email", "").lower() == email.lower():
                    return cid
            else:
                return cid
    return None

def get_or_create_client(name: str, email: str = None, company: str = None, phone: str = None, city: str = None, country: str = None, gstin: str = None) -> str:
    """
    Returns ClientID. If name exists but email differs, creates a new ID.
    Always uses the ClientID as the Primary Key.
    """
    existing_id = find_client_by_name_and_email(name, email)
    if existing_id:
        return existing_id

    # Create new client
    client_id = get_next_client_id()
    db = load_db()
    db["clients"][client_id] = {
        "id": client_id,
        "name": name,
        "email": email,
        "company": company,
        "phone": phone,
        "gstin": gstin,
        "address": {
            "city": city,
            "country": country
        },
        "created_at": datetime.now().isoformat(),
        "projects": [],
        "proposals": [],
        "invoices": [],
        "archived_chats": [],
        "preferences": {},
        "memory": ""
    }
    save_db(db)
    return client_id

def get_client(client_id: str) -> dict:
    """Retrieves a client record by its ID."""
    db = load_db()
    return db["clients"].get(client_id)

def save_proposal(client_id: str, proposal_metadata: dict, content: str, pdf_path: str, docx_path: str = None):
    """Saves a proposal link and metadata to the client record."""
    db = load_db()
    if client_id in db["clients"]:
        proposal_entry = {
            "proposal_id": f"PROP-{len(db['clients'][client_id]['proposals']) + 1001}",
            **proposal_metadata,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "pdf_path": pdf_path,
            "docx_path": docx_path
        }
        db["clients"][client_id]["proposals"].append(proposal_entry)
        save_db(db)

def get_next_invoice_number() -> str:
    """Increments and returns the next invoice number."""
    db = load_db()
    num = db.get("last_invoice_number", 1000) + 1
    db["last_invoice_number"] = num
    save_db(db)
    return f"INV-{num}"

def save_invoice(client_id: str, invoice_data: dict):
    """Saves an invoice to the client record."""
    db = load_db()
    if client_id in db["clients"]:
        db["clients"][client_id]["invoices"].append(invoice_data)
        save_db(db)

def update_client_field(client_id: str, field: str, value: any):
    """Updates a specific field for a client."""
    db_data = load_db()
    if client_id in db_data["clients"]:
        if "." in field:
            parts = field.split(".")
            target = db_data["clients"][client_id]
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value
        else:
            db_data["clients"][client_id][field] = value
        save_db(db_data)

def update_invoice_status(invoice_num: str, status: str):
    """Updates the status of an invoice."""
    db_data = load_db()
    for client in db_data["clients"].values():
        for inv in client["invoices"]:
            if inv["invoice_number"] == invoice_num:
                inv["status"] = status
                save_db(db_data)
                return True
    return False

def add_payment(invoice_num: str, amount: float, method: str):
    """Records a payment and updates pending status."""
    db_data = load_db()
    for client in db_data["clients"].values():
        for inv in client["invoices"]:
            if inv["invoice_number"] == invoice_num:
                payment_entry = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "amount": amount,
                    "method": method
                }
                inv.setdefault("payments", []).append(payment_entry)
                inv["total_paid"] = round(inv.get("total_paid", 0) + amount, 2)
                inv["total_pending"] = round(inv["grand_total"] - inv["total_paid"], 2)
                
                if inv["total_pending"] <= 0:
                    inv["status"] = "PAID"
                    inv["total_pending"] = 0
                else:
                    inv["status"] = "PARTIAL"
                
                # Regenerate PDF to reflect updated payment status
                try:
                    from documents.pdf_generator import generate_invoice_pdf
                    pdf_path = inv.get("file_path", f"documents/invoices/{invoice_num}.pdf")
                    invoice_for_pdf = {
                        **inv,
                        "client": client
                    }
                    generate_invoice_pdf(invoice_for_pdf, pdf_path)
                except Exception as e:
                    print(f"Failed to regenerate PDF on payment: {e}")
                
                save_db(db_data)
                return True
    return False

def log_project(client_id: str, project_data: dict):
    """Adds a new project to a client's history."""
    db_data = load_db()
    if client_id in db_data["clients"]:
        project_data.setdefault("status", "ACTIVE")
        project_data.setdefault("created_at", datetime.now().isoformat())
        db_data["clients"][client_id].setdefault("projects", []).append(project_data)
        save_db(db_data)
        return True
    return False

def update_project_status(client_id: str, title: str, status: str):
    """Updates the status of a specific project for a client."""
    db_data = load_db()
    if client_id in db_data["clients"]:
        for project in db_data["clients"][client_id].get("projects", []):
            if project["title"] == title:
                project["status"] = status
                save_db(db_data)
                return True
    return False

def delete_client_by_name(name: str) -> bool:
    """Deletes a client and all associated records (projects, invoices) by name."""
    db_data = load_db()
    
    client_id_to_delete = None
    for cid, client in db_data["clients"].items():
        if client["name"].lower() == name.lower():
            client_id_to_delete = cid
            break
            
    if client_id_to_delete:
        del db_data["clients"][client_id_to_delete]
        save_db(db_data)
        return True
    return False

def get_raw_database() -> dict:
    """Returns the entire database dictionary."""
    return load_db()
