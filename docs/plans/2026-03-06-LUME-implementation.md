# LUME Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Load executing-plans to implement this plan task-by-task.

**Goal:** Build a FastAPI-based personal administrative assistant for freelancers that automates proposals, invoices, and payment reminders.

**Architecture:** A single-backend application using OpenAI for intent detection/extraction and content generation, JSON for persistent storage, and SMTP for email delivery.

**Tech Stack:** FastAPI, OpenAI, ReportLab (PDF), python-docx (Word), python-dotenv, smtplib.

---

### Task 1: Project Scaffolding & Environment
Setup the directory structure and core dependencies.

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `app.py`

**Step 1: Create requirements.txt**
```text
fastapi
uvicorn
openai
python-dotenv
reportlab
python-docx
jinja2
```

**Step 2: Create .gitignore**
```text
.env
__pycache__/
*.pdf
*.docx
storage/data.json
```

**Step 3: Create .env.example**
```env
OPENAI_API_KEY=your_key_here
GMAIL_SENDER=name@gmail.com
GMAIL_APP_PASS=your_app_password
FREELANCER_NAME="Your Name"
```

**Step 4: Create basic app.py with health check**
```python
from fastapi import FastAPI
import os

app = FastAPI(title="LUME API")

# Ensure directories exist
os.makedirs("storage", exist_ok=True)
os.makedirs("documents", exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Step 5: Run to verify**
Run: `uvicorn app:app --reload`
Expected: Server starts and `http://localhost:8000/health` returns `{"status": "ok"}`

**Step 6: Commit**
```bash
git add requirements.txt .gitignore .env.example app.py
git commit -m "chore: initial project scaffolding"
```

---

### Task 2: Storage Layer
Implement the JSON-based data store.

**Files:**
- Create: `storage/db.py`
- Test: `tests/test_db.py`

**Step 1: Write a failing test for storage**
```python
import os
import json
from storage.db import load, save

def test_save_load():
    test_data = {"test": "data"}
    save(test_data)
    loaded = load()
    assert loaded == test_data
```

**Step 2: Implement storage/db.py**
Include `load`, `save`, and structure helpers from the design.
- **Indexing Requirement:** All clients must be stored under a unique `CLT-XXXX` key.
- **Helper:** Implement `get_next_client_id()` to return an incremental ID (starting at CLT-1001).
- **Helper:** Implement `find_client_by_name_and_email(name, email)` to detect duplicates or existing matches.
- **Helper:** Implement `get_or_create_client(name, email)` to centralize logic: search by name; if email differs, create new ID; if match, return ID.
- **Refactor:** Ensure `save_invoice`, `save_proposal`, and `log_reminder` accept `client_id` (not name) to avoid redundant lookup logic.

**Step 3: Run test**
Run: `pytest tests/test_db.py`
Expected: PASS

**Step 4: Commit**
```bash
git add storage/db.py tests/test_db.py
git commit -m "feat: implement JSON storage layer"
```

---

### Task 3: Intent Detection & Field Extraction
Logic to identify user needs and extract data from text.

**Files:**
- Create: `chatbot/llm.py`
- Create: `chatbot/intent.py`
- Test: `tests/test_intent.py`

**Step 1: Implement LLM Wrapper**
Create `chatbot/llm.py` with a `call_llm(prompt, model, json_mode)` function to centralize OpenAI client initialization and error handling.

**Step 2: Write tests for intent classification**
Mocks OpenAI response and verify intent labels.

**Step 3: Implement chatbot/intent.py**
Implement `detect_intent` and `extract_fields` using the `call_llm` wrapper.
- **Optional Logic:** Update `extract_fields` to look for `gstin`, `phone_number`, and `freelancer_background`.
- **Requirement:** Implement `keyword_detect` fallback logic (as per design) to handle cases where LLM is unavailable.
- **Conversational Cue:** If `gstin` or `phone_number` are missing, set a flag in `session_state` to trigger the bot to ask the user if they'd like to provide them.

**Step 4: Run tests**
Run: `pytest tests/test_intent.py`
Expected: PASS

**Step 5: Commit**
```bash
git add chatbot/llm.py chatbot/intent.py tests/test_intent.py
git commit -m "feat: add intent detection and field extraction"
```

---

### Task 4: Proposal Generation
Conversation flow for proposals and document creation.

**Files:**
- Create: `chatbot/proposal.py`
- Create: `documents/pdf_generator.py`
- Create: `documents/docx_generator.py`

**Step 1: Implement storage helpers for proposals**
Add `save_proposal(client_id, proposal_metadata, content)` and `save_project(client_id, project_data)` to `storage/db.py`. Ensure metadata includes `budget`, `timeline`, `deliverables`, and `background`.

**Step 2: Implement PDF & Word generators**
Build templates for ReportLab (PDF) and python-docx (Word).

**Step 3: Implement proposal_handler**
Manage multi-turn conversation, call generation logic, and save the generated proposal, project, and file paths to storage.
- **Requirement:** Use `storage.get_or_create_client` to handle client lookup/creation. Ask for email if creating a new client.
- **Requirement:** Inject `FREELANCER_NAME` from `.env` into the prompt context so the user isn't asked for it repeatedly.
- **Requirement:** Update `PROPOSAL_PROMPT` to instruct the LLM to match the tone to the project type (creative vs. technical).
- **Requirement:** The handler must generate both a PDF and a .docx file and provide links to both.

**Step 4: Implement Conversational Editing Loop**
Update `proposal_handler` to detect "refinement" messages after the initial draft.
- **Logic:** If the user sends a message while a draft is active, pass the `draft_content` + the user's `edit_instruction` to OpenAI to generate a revised version.
- **Regeneration:** Trigger the PDF and Word generators to overwrite the existing version of the file, to include the edits.

**Step 5: Implement validation logic**
Ensure generated proposals (including edits) meet word count (300+) and contain no placeholders before returning to user.

**Step 6: Verify document output**
Run a script to generate a dummy proposal and verify files exist in `documents/`.

**Step 7: Commit**
```bash
git add chatbot/proposal.py documents/
git commit -m "feat: implement proposal generation"
```

---

### Task 5: Invoice Generation & Part Payments
Calculations, invoice PDF creation, and payment tracking.

**Files:**
- Create: `chatbot/invoice.py`
- Modify: `documents/pdf_generator.py`

**Step 1: Implement calculation logic**
Write tests for tax, total, and **pending balance** calculations.

**Step 2: Implement invoice_handler**
Handle numbering, status management, and **recording part-payments**.
- **Requirement:** Use `storage.get_or_create_client` to link invoice to correct client.
- **Requirement:** Set default status to `UNPAID`.
- **Requirement:** After auto-generating an invoice number, ask the user for confirmation or if they'd like to provide a custom one.
- **Optional Fields:** Ensure the invoice PDF layout includes placeholders for GSTIN and Phone Number if provided. But if not provided, do not mention either of them on the invoice.
- **Layout Requirement:** The PDF must include "City, Country" address lines and a clearly labeled "NOTES:" section. Rename "Freelancer Payment Details" to "Freelancer Bank / Payment Details".

**Step 3: Update storage logic for payments**
Add a helper to record a payment: `add_payment(invoice_number, amount, method)`.
Ensure JSON schema supports `total_paid`, `total_pending`, and a `payments` array as per design.

**Step 4: Save Invoice Record**
Call the `storage.save_invoice()` helper to persist the generated invoice data to the JSON file.

**Step 5: Commit**
```bash
git add chatbot/invoice.py
git commit -m "feat: implement invoice module with part-payment tracking"
```

---

### Task 6: Payment Reminders & Gmail Integration
Automated follow-ups with dynamic pending amounts.

**Files:**
- Create: `chatbot/reminder.py`
- Create: `chatbot/gmail_sender.py`

**Step 1: Implement tone detection**
Logic for Gentle/Firm/Urgent based on due date.

**Step 2: Update reminder prompt for partials**
Ensure the `REMINDER_PROMPT` includes `{total_pending}` and clarifies that it's a balance follow-up.

**Step 3: Implement reminder_handler confirmation flow**
After generating a draft, display it and ask the user for confirmation (e.g., "Shall I send this?"). Only proceed on an affirmative response.

**Step 4: Implement Gmail SMTP sender**
Create `chatbot/gmail_sender.py` using `smtplib` and `.env` credentials.

**Step 5: Log reminder**
Call storage helper `log_reminder` to record the sent email timestamp and tone in the invoice record.

**Step 6: Commit**
```bash
git add chatbot/reminder.py chatbot/gmail_sender.py
git commit -m "feat: implement reminders with partial balance awareness"
```

---

### Task 7: Query Handling
Implement logic to answer user questions about data.

**Files:**
- Create: `chatbot/query.py`

**Step 1: Implement query_handler**
Connect `QUERY` intent to storage helpers for both data retrieval (e.g., `get_unpaid_invoices`) and data modification (e.g., `update_invoice_status`).

**Step 2: Commit**
```bash
git add chatbot/query.py
git commit -m "feat: implement data query handler"
```

---

### Task 8: Chat UI & Integration
Build the premium visual interface and link to backend.

**Files:**
- Create: `templates/index.html`
- Create: `static/style.css`
- Modify: `app.py`

**Step 1: Implement /chat endpoint**
Link all modules together in the main FastAPI app.
Mount `documents/` directory as static files to allow PDF/Word downloads.

**Step 2: Build Glassmorphism UI**
Premium design as requested.
- **Requirement:** Implement a "typing indicator" to show when the bot is processing.
Implement the creative vision as defined in [UI_SPECIFICATION.md](file:///Users/ssrrattan/Documents/LUME/UI_SPECIFICATION.md) ("The Editorial Glass").
- **Requirement:** Implement a "typing indicator" and "Lume-inance" light source effect.
- **Requirement:** After displaying a generated proposal or reminder draft, provide a text area to allow the user to edit the content before it is finalized (downloaded or sent).
- **Requirement:** Show inline "Download PDF" / "Download Word" buttons for generated documents.
- **Requirement:** Show a "Send via Email" button for payment reminder drafts.

**Step 3: Manual Verification**
Full end-to-end test of the bot.
