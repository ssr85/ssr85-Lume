# Invoice Generation

## Overview

When the intent is `INVOICE`, the chatbot collects work details through conversation, calculates all totals, auto-generates an invoice number, and produces a professionally formatted downloadable PDF.

---

## Required and Optional Fields

| Field | Description | Required |
|---|---|---|
| Client Name | Who is being billed | Yes |
| Project Name | What project this invoice is for | Yes |
| Invoice Number | Auto-generated (overridable) | Yes |
| Invoice Date | Date of invoice (defaults to today) | Yes |
| Due Date | Payment due date | Yes |
| Work Items | Description of each item or milestone | Yes |
| Hours per Item | Hours logged per line item | Yes |
| Rate | Hourly rate or fixed fee per item | Yes |
| Freelancer Payment Details | Bank or payment method info | Yes |
| Tax / GST | Tax percentage if applicable | Optional |
| Notes | Additional message on the invoice | Optional |

---

## Invoice Calculation

```python
def calculate_invoice(items: list, tax_percent: float = 0) -> dict:
    subtotals = []
    for item in items:
        subtotal = item["hours"] * item["rate"]
        subtotals.append(subtotal)
        item["subtotal"] = subtotal

    total_before_tax = sum(subtotals)
    tax_amount = round(total_before_tax * (tax_percent / 100), 2)
    grand_total = round(total_before_tax + tax_amount, 2)

    return {
        "items": items,
        "subtotal": total_before_tax,
        "tax_percent": tax_percent,
        "tax_amount": tax_amount,
        "grand_total": grand_total
    }
```

### Example Calculation

| Item | Hours | Rate | Subtotal |
|---|---|---|---|
| Website Design | 10 | $80 | $800 |
| Development | 8 | $80 | $640 |
| **Subtotal** | | | **$1,440** |
| **GST (10%)** | | | **$144** |
| **Grand Total** | | | **$1,584** |

---

## Invoice Numbering

Invoice numbers are auto-generated sequentially and persisted in storage:

```python
def get_next_invoice_number() -> str:
    data = storage.load()
    last_num = data.get("last_invoice_number", 1000)
    new_num = last_num + 1
    storage.update("last_invoice_number", new_num)
    return f"INV-{new_num}"
```

The freelancer can override this with a custom number:
```
"Create invoice number 2024-005 for..."
  Uses: INV number 2024-005
```

---

## Invoice Status

All invoices are created with status `UNPAID` by default:

```python
INVOICE_STATUSES = ["UNPAID", "PAID", "OVERDUE"]
```

Status can be updated through chat:
```
"Mark invoice #INV-1043 as paid"
  storage.update_invoice_status("INV-1043", "PAID")
```

An invoice automatically becomes `OVERDUE` when status is still `UNPAID` and today's date is past the `due_date`. This check runs every time invoices are loaded.

---

## Invoice PDF Layout

Generated using **ReportLab**. The invoice must include:

```
+-------------------------------------------------------+
|  [FREELANCER NAME]                                    |
|  [Email] - [Phone]                                    |
|  [City], [Country]                                    |
|                         Invoice #: INV-1043           |
|                         Date: [Invoice Date]          |
|                         Due Date: [Due Date]          |
+-------------------------------------------------------+
|  BILL TO:                                             |
|  [Client Name]                                        |
|  [Client Company]                                     |
|  [Client Email]                                       |
|  GSTIN: [Optional] | Phone: [Optional]                |
+-------------------------------------------------------+
|  # | Description        | Hrs |  Rate  | Amount       |
|  1 | Website Design     |  10 |  $80   | $800         |
|  2 | Development        |   8 |  $80   | $640         |
+-------------------------------------------------------+
|                         Subtotal:      $1,440         |
|                         Tax (10%):     $144           |
|                         Total Amount:  $1,584         |
|                         Amount Paid:   $400           |
|                         PENDING DUE:   $1,184         |
+-------------------------------------------------------+
|  PAYMENT DETAILS                                      |
|  [Bank name, account number, or payment link]         |
|                                                       |
|  [Notes if any]                                       |
+-------------------------------------------------------+
```

---

## Storage

Each invoice is saved to the client's record:

```json
{
  "invoice_number": "INV-1043",
  "project_name": "PeakForm Social Campaign",
  "invoice_date": "2026-03-01",
  "due_date": "2026-03-16",
  "items": [
    { "description": "Social content creation", "hours": 18, "rate": 100, "subtotal": 1800 }
  ],
  "tax_percent": 0,
  "tax_amount": 0,
  "grand_total": 1800,
  "total_paid": 400,
  "total_pending": 1400,
  "payments": [
    { "amount": 400, "date": "2026-03-05", "method": "Bank Transfer" }
  ],
  "status": "PARTIAL",
  "reminders_sent": [],
  "file_path": "documents/invoices/INV-1043.pdf"
}
```
