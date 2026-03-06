# Data Storage

## Overview

All project data is stored in a **JSON file** or **SQLite database**. No cloud database is required. Data persists between sessions by loading at startup and writing to disk on every update.

---

## Storage Options

| Option | When to Use | File |
|---|---|---|
| **JSON** | Simple projects, easier to read and debug | `storage/data.json` |
| **SQLite** | If you need queries, filtering, or larger datasets | `storage/data.db` |

Both are acceptable. JSON is recommended for simplicity.

---

## JSON Schema

The entire data store is structured around clients. Each client contains their projects, proposals, invoices, and reminder history as nested arrays.

```json
{
  "last_invoice_number": 1043,
  "last_client_id": 1001,
  "clients": {
    "CLT-1001": {
      "id": "CLT-1001",
      "name": "PeakForm",
      "email": "contact@peakform.com",
      "company": "PeakForm Ltd",
      "phone": "+1 555 000 1234",
      "created_at": "2026-02-01T10:00:00",
      "projects": [
        {
          "project_id": "proj-001",
          "project_name": "Social Media Campaign",
          "description": "3-week social media campaign",
          "status": "active",
          "created_at": "2026-02-01T10:00:00"
        }
      ],
      "proposals": [
        {
          "proposal_id": "prop-001",
          "project_title": "Social Media Campaign",
          "project_description": "3-week social media campaign",
          "deliverables": "Logo, Brand Guidelines, 5 Post Templates",
          "timeline": "3 weeks",
          "budget": "$1500",
          "freelancer_background": "5 years experience in social branding",
          "content": "...",
          "created_at": "2026-02-01T10:05:00",
          "file_path": "documents/proposals/peakform-social-proposal.pdf"
        }
      ],
      "invoices": [
        {
          "invoice_number": "INV-1043",
          "project_name": "Social Media Campaign",
          "invoice_date": "2026-02-14",
          "due_date": "2026-03-01",
          "items": [
            {
              "description": "Social content creation",
              "hours": 18,
              "rate": 100,
              "subtotal": 1800
            }
          ],
          "tax_percent": 0,
          "tax_amount": 0,
          "grand_total": 1800,
          "status": "UNPAID",
          "payment_details": "Bank: HDFC, A/C: XXXX",
          "notes": "",
          "reminders_sent": [
            {
              "sent_at": "2026-03-06T10:30:00",
              "tone": "firm",
              "recipient": "contact@peakform.com",
              "subject": "Follow-Up on Invoice #INV-1043",
              "days_overdue_at_send": 5
            }
          ],
          "file_path": "documents/invoices/INV-1043.pdf"
        }
      ]
    }
  }
}
```

---

## Storage Helper Functions (`storage/db.py`)

```python
import json
import os
from datetime import date

DATA_FILE = "storage/data.json"

def load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"last_invoice_number": 1000, "last_client_id": 1000, "clients": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_client(client_id: str) -> dict:
    data = load()
    return data["clients"].get(client_id)

def get_or_create_client(name: str, email: str) -> str:
    """Returns ClientID. Creates new if name match has different email."""
    data = load()
    # Search logic here...
    return client_id

def save_invoice(client_id: str, invoice: dict):
    data = load()
    data["clients"][client_id]["invoices"].append(invoice)
    save(data)

def update_invoice_status(invoice_number: str, new_status: str) -> bool:
    data = load()
    for client in data["clients"].values():
        for inv in client.get("invoices", []):
            if inv["invoice_number"] == invoice_number:
                inv["status"] = new_status
                save(data)
                return True
    return False

def get_unpaid_invoices() -> list:
    data = load()
    unpaid = []
    today = date.today()
    for client in data["clients"].values():
        for inv in client.get("invoices", []):
            if inv["status"] in ("UNPAID", "OVERDUE"):
                due = date.fromisoformat(inv["due_date"])
                if today > due and inv["status"] == "UNPAID":
                    inv["status"] = "OVERDUE"
                unpaid.append({**inv, "client_name": client["name"]})
    save(data)
    return unpaid

def get_next_invoice_number() -> str:
    data = load()
    num = data.get("last_invoice_number", 1000) + 1
    data["last_invoice_number"] = num
    save(data)
    return f"INV-{num}"

def log_reminder(client_name: str, invoice_number: str, log_entry: dict):
    data = load()
    key = client_name.lower().replace(" ", "")
    for inv in data["clients"][key]["invoices"]:
        if inv["invoice_number"] == invoice_number:
            inv["reminders_sent"].append(log_entry)
            save(data)
            return
```

---

## Data Types Stored

| Data Type | Description |
|---|---|
| **Client Records** | Name, email, company, phone, created date |
| **Projects** | Project name, client, description, status |
| **Proposals** | Full proposal text, linked client and project, file path |
| **Invoices** | All fields, line items, totals, due date, status, reminders sent |
| **Payment Reminders** | Sent timestamp, tone, recipient, subject, days overdue at send |

---

## Invoice Status Values

| Status | Meaning |
|---|---|
| `UNPAID` | Created, not yet paid, not past due date |
| `OVERDUE` | Past due date and still unpaid (auto-set on load) |
| `PAID` | Manually marked as paid by the freelancer through chat |

---

## Querying Data Through Chat

| Chat Input | Storage Action |
|---|---|
| "Show all unpaid invoices" | `get_unpaid_invoices()` |
| "Mark invoice #INV-1043 as paid" | `update_invoice_status("INV-1043", "PAID")` |
| "Show me everything I sent to BrightLeaf" | `get_client("BrightLeaf")` -- returns proposals, invoices, reminders |
| "What's the status of the PeakForm invoice?" | Look up invoice by client name |
