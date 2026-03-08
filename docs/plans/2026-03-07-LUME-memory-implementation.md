# Memory Management System Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Load executing-plans to implement this plan task-by-task.

**Goal:** Implement a memory management system to archive chats and extract long-term client context (preferences and memory) for LUME.

**Architecture:** We will update the JSON schema, add an archive endpoint, use the LLM to extract data from transcripts, inject that context into the intent prompt, and add an "Archive" button to the UI.

**Tech Stack:** Python (FastAPI), HTML/JS, OpenAI (via existing wrapper), local JSON storage (`db.py`).

---

### Task 1: Update Database Schema & Accessors

**Files:**
- Modify: `storage/db.py`

**Step 1: Write minimal implementation**

Update `get_or_create_client` in `storage/db.py` to include new initial fields:
```python
        "created_at": datetime.now().isoformat(),
        "projects": [],
        "proposals": [],
        "invoices": [],
        "archived_chats": [],     # NEW
        "preferences": {},        # NEW
        "memory": ""              # NEW
```

**Step 2: Commit**
```bash
git add storage/db.py
git commit -m "feat(db): add memory and preferences fields to client schema"
```

---

### Task 2: Create the Memory Extraction Module

**Files:**
- Create: `chatbot/memory.py`

**Step 1: Write the implementation**

Create `chatbot/memory.py` with an `archive_chat(thread_id: str, client_id: str)` function.
1. Fetch thread from `storage.chats.get_thread(thread_id)`.
2. Format the messages into a single text transcript.
3. Call the existing LLM API (e.g., via `chatbot.llm.generate_structured_response` or `ask_openai` if structured wrapper isn't available) with a system prompt: "Analyze this client chat transcript. Extract updated contact info (email, phone, company, address), define their preferences (e.g., communication style), and note any unstructured memory/rules of engagement. Also provide a 1-sentence summary of the chat. Output as JSON with keys: email, phone, company, city, country, gstin, preferences (dict), memory (string), summary (string)."
4. Parse the LLM JSON response.
5. Fetch the client from `db.get_client(client_id)`.
6. Update the client's fields using `db.update_client_field` for new info (only overwrite if the LLM provided a non-empty value).
7. Handle `preferences` (merge dicts).
8. Append the `summary` to `archived_chats` with the `thread_id` and current timestamp.
9. Append `memory` string to the existing client `memory`.

**Step 2: Commit**
```bash
git add chatbot/memory.py
git commit -m "feat(llm): implement chat archiving and memory extraction logic"
```

---

### Task 3: Create API Endpoint for Archiving

**Files:**
- Modify: `app.py`

**Step 1: Write the implementation**

Add to `app.py`:
```python
from chatbot.memory import archive_chat

class ArchiveRequest(BaseModel):
    client_id: str

@app.post("/api/chats/{thread_id}/archive")
async def archive_chat_endpoint(thread_id: str, req: ArchiveRequest):
    try:
        success = archive_chat(thread_id, req.client_id)
        if success:
            return {"status": "success", "message": "Chat archived and memory updated."}
        else:
            return {"status": "error", "message": "Failed to archive chat. Client not found or LLM error."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```
*(Make sure `archive_chat` returns a boolean indicating success).*

**Step 2: Commit**
```bash
git add app.py
git commit -m "feat(api): add endpoint to archive chat thread"
```

---

### Task 4: UI Integration for Archive Button

**Files:**
- Modify: `templates/index.html`

**Step 1: Write the implementation**

1. In the sidebar where chat threads are listed (likely rendered via JS `renderChats` or Alpine.js in `index.html`), add an "Archive" button next to each thread or a global "Archive Current Chat" button.
2. Given the current setup, add a button to the top right of the main chat area: `<button onclick="archiveCurrentChat()" class="...">Archive Chat</button>`.
3. Add a JS function `archiveCurrentChat()` that reads the `current_thread_id` and the `selected_client_id` (from the UI dropdown or state), and POSTs to `/api/chats/{thread_id}/archive`.
4. Show an alert or toast on success/failure.

**Step 2: Commit**
```bash
git add templates/index.html
git commit -m "feat(ui): add archive chat button and api call"
```

---

### Task 5: Context Injection into Intent Prompt

**Files:**
- Modify: `chatbot/intent.py` (or where the LLM prompt is constructed)

**Step 1: Write the implementation**

When generating a response for the user, retrieve the `client_id` from the session (if a client is selected).
Fetch the client from `storage.db.get_client(client_id)`.
Extract `preferences` and `memory`.
Prepend/Append to the system prompt:
```text
CLIENT CONTEXT:
Memory: {client['memory']}
Preferences: {json.dumps(client['preferences'])}
You MUST adhere to these preferences and take this memory into account when assisting with this client.
```

**Step 2: Commit**
```bash
git add chatbot/intent.py 
# (or app.py / chatbot/*.py depending on where system prompts are built)
git commit -m "feat(llm): inject client memory and preferences into context window"
```

---

### Verification Plan

Since there are no existing automated tests, we will verify manually.

1. Start application (`python app.py`).
2. Create or select a client. Provide new information in chat, e.g., "Note: this client prefers emails at 9 AM only."
3. Click "Archive Chat".
4. Check network tab for 200 OK on `/api/chats/.../archive`.
5. Open `storage/data.json` and verify the client's `memory` field contains "prefers emails at 9 AM only" and `archived_chats` contains the chat summary.
6. Start a new chat with the same client and ask "When does this client prefer emails?". Verify the LLM answers correctly based on injected memory.
