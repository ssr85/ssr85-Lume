# Freelancer Admin Automation Chatbot

> AI-powered personal admin assistant for freelancers -- Proposals | Invoices | Payment Reminders | Gmail Integration

---

## Overview

Freelancers lose significant unpaid time every week writing proposals, generating invoices, and chasing payments. This chatbot replaces all three tasks with a single conversational interface powered by an LLM. Instead of switching between tools, the freelancer simply describes what they need in plain language and the bot handles the rest.

---

## Features

| Feature | Description |
|---|---|
| **Proposal Generator** | Generates full professional proposals from a short project brief |
| **Invoice Generator** | Creates formatted, downloadable PDF invoices from logged hours and rates |
| **Payment Reminder** | Drafts tone-adjusted reminders and sends them directly via Gmail |
| **Memory Management** | Archives chats to remember client "rules", preferences, and history |
| **Client Data Management** | Stores clients, projects, invoices, and interaction memory |
| **Invoice Status Tracking** | Mark invoices as paid/unpaid/overdue through chat |

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python (FastAPI) |
| LLM | OpenAI (GPT-4o) |
| PDF Generation | ReportLab |
| Word Generation | python-docx |
| Email | smtplib + Gmail App Password |
| Frontend | HTML / CSS / JS (Glassmorphism UI) |
| Storage | JSON file (`storage/data.json`) |

---

## Project Structure

```
freelancer-chatbot/
|-- app.py                  # Main FastAPI app
|-- chatbot/
|   |-- llm.py              # LLM wrapper (OpenAI client)
|   |-- intent.py           # Intent detection logic
|   |-- proposal.py         # Proposal generation & editing loop
|   |-- invoice.py          # Invoice generation & part-payments
|   |-- reminder.py         # Payment reminder logic
|   |-- query.py            # Data query handler
|   |-- memory.py           # extraction of client context & rules
|   +-- gmail_sender.py     # Gmail send via smtplib
|-- storage/
|   |-- db.py               # JSON storage helpers (ClientID PK)
|   +-- data.json           # Persistent data store (ignored)
|-- documents/
|   |-- pdf_generator.py    # ReportLab PDF logic
|   +-- docx_generator.py   # python-docx Word logic
|-- static/                 # Glassmorphism CSS & JS
|-- templates/
|   +-- index.html          # Chat interface
|-- .env                    # Credentials (ignored)
|-- requirements.txt
+-- README.md
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/your-username/freelancer-chatbot.git
cd freelancer-chatbot
pip install -r requirements.txt
```

### 2. Configure Gmail

See [GMAIL_SETUP.md](GMAIL_SETUP.md) for full instructions.

Create a `.env` file:

```env
GMAIL_SENDER=yourname@gmail.com
GMAIL_APP_PASS=your-16-char-app-password
```

### 3. Run the app

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

---

## Usage Examples

```
"I need a proposal for a 3-week social media campaign for PeakForm"
  Triggers: Proposal Generator

"Create an invoice for 18 hours at $100/hr for TechStart"
  Triggers: Invoice Generator

"PeakForm still hasn't paid -- invoice is 10 days overdue"
  Triggers: Payment Reminder + Gmail Send

"Show me all unpaid invoices"
  Triggers: Invoice Status Query

"Note: Sarah at BrightLeaf hates being called on Mondays"
  Triggers: Memory Archival (when Archived)

"How should I approach the next email to PeakForm?"
  Triggers: Injected Context Reasoning
```

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) -- System design and component overview
- [INTENT_DETECTION.md](INTENT_DETECTION.md) -- How the chatbot routes requests
- [PROPOSAL_GENERATION.md](PROPOSAL_GENERATION.md) -- Proposal prompting and structure
- [INVOICE_GENERATION.md](INVOICE_GENERATION.md) -- Invoice calculation and numbering
- [PAYMENT_REMINDERS.md](PAYMENT_REMINDERS.md) -- Reminder tone logic and send flow
- [GMAIL_SETUP.md](GMAIL_SETUP.md) -- Gmail App Password configuration
- [DATA_STORAGE.md](DATA_STORAGE.md) -- Storage schema and retrieval
- [memory.md](memory.md) -- Rules and logic for client memory management
