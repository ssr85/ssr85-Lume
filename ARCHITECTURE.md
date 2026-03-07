# System Architecture

## Overview

The Freelancer Admin Chatbot follows a single-backend, single-frontend architecture. All user interaction happens through one chat interface. The backend routes each message to the appropriate feature module based on detected intent.

---

## Architecture Diagram

```
+----------------------------------------------------------+
|                     Browser (Chat UI)                    |
|          HTML / CSS / JS -- Glassmorphism Chat           |
+-------------------------+--------------------------------+
                          | HTTP POST /chat
                          v
+----------------------------------------------------------+
|                      FastAPI Backend                     |
|                                                          |
|   +--------------------------------------------------+   |
|   |              Intent Detector                     |   |
|   |   Reads user message -> identifies feature       |   |
|   +-------+----------+----------+-------------------+   |
|           |          |          |                        |
|           v          v          v                        |
|   +----------+ +---------+ +----------------------+      |
|   | Proposal | | Invoice | | Payment Reminder     |      |
|   | + Editing| | + Part-P| | + Gmail Send Module  |      |
|   | + Gmail  | | + Gmail | |                      |      |
|   +-----+----+ +----+----+ +----------+-----------+      |
|         |           |                 |                   |
|         v           v                 v                   |
|   +--------------------------------------------------+   |
|   |           LLM Wrapper (chatbot/llm.py)           |   |
|   |              OpenAI GPT-4o Client                |   |
|   +--------------------------------------------------+   |
|                                                          |
|   +--------------------------------------------------+   |
|   |         Document Generator                       |   |
|   |   ReportLab (PDF) & python-docx (Word)           |   |
|   +-----------------------+--------------------------+   |
|                           |                              |
|                           v                              |
|   +--------------------------------------------------+   |
|   |         Gmail Sender (smtplib)                   |   |
|   |   Sends emails (reminders/invoices/proposals)    |   |
|   +--------------------------------------------------+   |
|                                                          |
|   +--------------------------------------------------+   |
|   |         Storage Layer (storage/db.py)            |   |
|   |   JSON file (ClientID as Primary Key)            |   |
|   +--------------------------------------------------+   |
+----------------------------------------------------------+
```

---

## Request Lifecycle

1. Freelancer types a message in the chat UI
2. Frontend sends a `POST /chat` request with the message and session history
3. Backend passes the message to the **Intent Detector**
4. Intent Detector classifies the request (proposal / invoice / reminder / query)
5. The matched module collects any missing fields through follow-up questions
6. Once all required fields are available, the LLM API is called to generate content
7. Generated content is returned to the chat as a preview
8. If a document is generated, the **Document Generator** creates a PDF/Word file and returns a download link
9. If a reminder, invoice, or proposal is confirmed for sending, the **Gmail Sender** dispatches the email and logs the event
10. All relevant data is saved to the **Storage Layer**

---

## Module Responsibilities

### `chatbot/intent.py`
- Classifies incoming messages into one of four intents
- Uses prompt-based classification via the LLM or keyword matching as fallback
- See [INTENT_DETECTION.md](INTENT_DETECTION.md)

### `chatbot/proposal.py`
- Manages multi-turn collection of proposal fields
- Calls the LLM with a structured prompt to generate a full proposal
- Triggers Gmail send for proposal delivery
- See [PROPOSAL_GENERATION.md](PROPOSAL_GENERATION.md)

### `chatbot/invoice.py`
- Collects invoice fields through conversation
- Performs all calculations (subtotal, tax, grand total)
- Auto-generates sequential invoice numbers
- Triggers Gmail send for invoice delivery
- See [INVOICE_GENERATION.md](INVOICE_GENERATION.md)

### `chatbot/reminder.py`
- Detects overdue duration and selects tone level
- Generates reminder with LLM and presents draft in chat
- Triggers Gmail send on freelancer confirmation
- See [PAYMENT_REMINDERS.md](PAYMENT_REMINDERS.md)

### `chatbot/llm.py`
- Centralized wrapper for OpenAI client.
- Handles prompts, model selection, and error handling.

### `storage/db.py`
- Read/write helpers for the JSON store.
- Manages **ClientID** (Incremental PK) and data integrity.
- See [DATA_STORAGE.md](DATA_STORAGE.md)

### `documents/pdf_generator.py`
- Generates professionally formatted invoice and proposal PDFs using ReportLab

### `documents/docx_generator.py`
- Generates .docx proposal documents using python-docx

---

## Session State

Each chat session maintains a `state` dictionary that tracks:

```python
session_state = {
    "intent": None,              # Current active intent
    "collected_fields": {},      # Fields gathered so far
    "pending_fields": [],        # Fields still needed
    "draft_content": None,       # Generated draft awaiting confirmation
    "awaiting_confirmation": False
}
```

This allows the bot to pick up mid-conversation without losing context.
