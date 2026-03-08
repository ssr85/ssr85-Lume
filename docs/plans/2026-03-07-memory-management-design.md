# Memory Management System Design

## Overview
Currently, LUME operates with limited long-term memory. It doesn't systematically learn from past interactions to improve future responses for specific clients. This design outlines a Memory Management System to solve this by archiving chats and extracting persistent client context.

## User Review Required
No major breaking changes. The approach involves adding a manual "Archive" button to the UI that processes the chat and updates the client's database record.

## Proposed Changes

### Database Schema Update (`storage/data.json` & `db.py`)
- We will expand the client schema in `data.json` to include:
  - `archived_chats`: Array of objects storing past interactions (`{"date": "...", "summary": "...", "thread_id": "..."}`)
  - `preferences`: Dictionary for structured preferences (e.g., contact method, tone).
  - `memory`: String for unstructured context (e.g., "Client prefers weekend emails, always CCs their manager").
- Update `db.py` to handle updating these new fields cleanly.

### Archival & Extraction Logic (`chatbot/memory.py` [NEW])
- Create a new module `memory.py` with the core logic.
- **Workflow:**
  1. Triggered by a new API endpoint (e.g., `POST /api/chats/{thread_id}/archive`).
  2. The endpoint retrieves the full transcript from `chats.json`.
  3. The transcript is sent to the LLM with a strict prompt to extract updated client details (email, phone, etc.), deduce preferences/rules of engagement, and summarize the interaction.
  4. The returned JSON is parsed and `storage/data.json` is updated via `db.py`.

### UI Integration (`templates/index.html` & `static/js/app.js`)
- Add an "Archive" button next to each chat thread in the sidebar.
- Wire the button to call the new `/api/chats/{thread_id}/archive` endpoint and display a success/failure toast.

### Context Injection Logic (`chatbot/intent.py` & `app.py`)
- When a client is identified (either explicitly selected or mentioned), their full profile, including `preferences` and `memory`, must be fetched from the DB.
- This profile data will be injected into the system prompt for the current session, ensuring the LLM relies on past context for its responses.

## Verification Plan
### Manual Verification
1. Open the UI, select a client, and have a conversation where new information is provided (e.g., "Please always email me on Fridays from now on").
2. Click the "Archive" button for that chat thread.
3. Inspect `storage/data.json` to verify the `preferences` or `memory` field for that client has been updated.
4. Start a *new* chat thread with the same client and ask "When should I email you?". The bot should answer using the newly archived memory.
