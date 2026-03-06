# Chat History & UI Overhaul Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Load executing-plans to implement this plan task-by-task.

**Goal:** Implement a persistent chat history sidebar and overhaul the UI to a premium 3-pane glassmorphism layout lighter colours.

**Architecture:** Create a new `storage/chats.py` to manage `chats.json`. Update `app.py` to serve chat history. Rewrite `index.html` and `style.css` to remove the Bento grid and implement the sidebar. Update `script.js` to manage thread state.

**Tech Stack:** Python (FastAPI), HTML, CSS, JavaScript.

---

### Task 1: Chat Storage Backend (`storage/chats.py`)

**Files:**
- Create: `storage/chats.py`
- Create (implicit): `storage/chats.json`

**Step 1: Write storage implementation**

Create `storage/chats.py` with the following content:
```python
import json
import os
from datetime import datetime

CHATS_FILE = "storage/chats.json"

def load_chats() -> dict:
    if not os.path.exists(CHATS_FILE):
        return {"current_id": 0, "threads": {}}
    try:
        with open(CHATS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"current_id": 0, "threads": {}}

def save_chats(data: dict):
    with open(CHATS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def create_thread(title: str = "New Chat") -> str:
    data = load_chats()
    data["current_id"] += 1
    thread_id = f"thread_{data['current_id']}"
    data["threads"][thread_id] = {
        "id": thread_id,
        "title": title,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "messages": []
    }
    save_chats(data)
    return thread_id

def append_message(thread_id: str, role: str, content: str):
    data = load_chats()
    if thread_id in data["threads"]:
        data["threads"][thread_id]["messages"].append({"role": role, "content": content})
        data["threads"][thread_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
        save_chats(data)

def get_thread(thread_id: str) -> dict:
    data = load_chats()
    return data["threads"].get(thread_id)

def get_all_threads() -> list:
    data = load_chats()
    threads = list(data["threads"].values())
    threads.sort(key=lambda x: x["updated_at"], reverse=True)
    return [{"id": t["id"], "title": t["title"], "updated_at": t["updated_at"]} for t in threads]
```

### Task 2: Backend API Endpoints (`app.py` & `query.py`)

**Files:**
- Modify: `app.py`
- Modify: `chatbot/query.py`

**Step 1: Update API endpoints in `app.py`**

Add imports and endpoints:
```python
from storage import db, chats

# Add these new endpoints before `if __name__ == "__main__":`

@app.get("/api/chats")
async def get_chats():
    return {"status": "success", "threads": chats.get_all_threads()}

@app.get("/api/chats/{thread_id}")
async def get_chat_thread(thread_id: str):
    thread = chats.get_thread(thread_id)
    if thread:
        return {"status": "success", "thread": thread}
    return {"status": "error", "message": "Thread not found"}
```

Modify the `/chat` endpoint to handle `thread_id`:
```python
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    thread_id = data.get("thread_id")
    
    if not thread_id:
        # Title can be generated later by an LLM, for now just first few words
        title = " ".join(message.split()[:3]) + "..."
        thread_id = chats.create_thread(title)
        
    chats.append_message(thread_id, "user", message)
```

Pass `thread_id` to the session:
```python
    session["thread_id"] = thread_id
```

**Step 2: Update `query.py` logic**

Instead of keeping history in `session`, fetch it from `chats.py`:
```python
from storage import db, chats

def query_handler(message: str, session: dict):
    # ... prompt logic ...
    
    thread_id = session.get("thread_id")
    history = []
    if thread_id:
        thread = chats.get_thread(thread_id)
        if thread:
            # Get last 6 messages excluding the one just added
            history = thread["messages"][-7:-1] 

    response = call_llm(prompt, history=history)
    # ... action logic ...

    # Instead of session history appending:
    if thread_id:
        chats.append_message(thread_id, "assistant", final_text)
        
    return final_text
```
*(Also clean up the old `session["query_history"]` code).*

### Task 3: HTML Layout Re-write (`templates/index.html`)

**Files:**
- Modify: `templates/index.html`

**Step 1: Write structure**
Replace the `.bento-grid` entirely with the new layout.
```html
<div class="app-layout">
    <header class="top-nav">
        <h1>Ask <span class="text-glow">LUME</span></h1>
        <button class="nav-menu-btn">≡</button>
    </header>

    <div class="main-container">
        <!-- Sidebar -->
        <aside class="sidebar block-panel">
            <div class="sidebar-header">
                <h2>Chat History</h2>
                <button id="new-chat-btn" class="icon-btn" title="New Chat">＋</button>
            </div>
            <div class="history-list" id="history-list">
                <!-- Dynamically populated -->
            </div>
        </aside>

        <!-- Chat Area -->
        <main class="chat-area block-panel">
            <div class="chat-header">
                <h2>Agency Chat</h2>
            </div>
            <div id="chat-window">
                <!-- Chat bubbles -->
            </div>
            <div class="input-area">
                <div class="glass-input">
                    <input type="text" id="user-input" placeholder="Enter command..." autocomplete="off">
                    <button id="send-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z" />
                        </svg>
                    </button>
                </div>
            </div>
        </main>
    </div>
</div>
```
Ensure the modal HTML is preserved at the bottom.

### Task 4: CSS Styling (`static/style.css`)

**Files:**
- Modify: `static/style.css`

**Step 1: Update styles**
Replace `.bento-grid` and card styles with the new layout styles.
```css
.app-layout {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 1rem 2rem;
    gap: 1rem;
    z-index: 10;
}

.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(42, 86, 255, 0.3);
    border-radius: 12px;
    box-shadow: 0 0 15px rgba(42, 86, 255, 0.1);
}

.top-nav h1 {
    font-family: var(--headline-serif);
    font-weight: 400;
    font-size: 1.8rem;
}

.text-glow {
    color: #4A72FF;
    text-shadow: 0 0 10px rgba(74, 114, 255, 0.5);
}

.main-container {
    display: flex;
    flex: 1;
    gap: 1.5rem;
    overflow: hidden;
}

.block-panel {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    display: flex;
    flex-direction: column;
}

.sidebar {
    width: 320px;
    padding: 1.5rem;
}

.sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.sidebar-header h2 {
    font-size: 1.2rem;
    font-weight: 300;
}

.icon-btn {
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    opacity: 0.7;
}

.icon-btn:hover {
    opacity: 1;
}

.history-item {
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 0.5rem;
    cursor: pointer;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid transparent;
    transition: all 0.2s;
}

.history-item:hover, .history-item.active {
    background: rgba(42, 86, 255, 0.1);
    border-color: rgba(42, 86, 255, 0.3);
    box-shadow: 0 0 10px rgba(42, 86, 255, 0.1);
}

.history-date {
    font-size: 0.7rem;
    color: var(--text-dim);
    margin-bottom: 0.2rem;
}

.chat-area {
    flex: 1;
    padding: 1.5rem;
}

.chat-header {
    margin-bottom: 1rem;
    border-bottom: 1px solid var(--card-border);
    padding-bottom: 1rem;
}

.bot-card {
    background: transparent;
    border: 1px solid rgba(42, 86, 255, 0.4);
    box-shadow: inset 0 0 20px rgba(42, 86, 255, 0.1), 0 0 15px rgba(42, 86, 255, 0.1);
}

.user-card {
    background: rgba(255, 255, 255, 0.08); /* Muted slate for user per screenshot */
    border: none;
    box-shadow: none;
}
```

### Task 5: Frontend JS Logic (`script.js`)

**Files:**
- Modify: `static/script.js`

**Step 1: Rewrite logic to support threads**

Add global `currentThreadId = null;`. 

Function to load history:
```javascript
async function loadChatHistory() {
    const res = await fetch('/api/chats');
    const data = await res.json();
    const list = document.getElementById('history-list');
    list.innerHTML = '';
    
    data.threads.forEach(t => {
        const div = document.createElement('div');
        div.className = `history-item ${t.id === currentThreadId ? 'active' : ''}`;
        div.onclick = () => selectThread(t.id);
        
        const date = new Date(t.updated_at).toLocaleDateString();
        div.innerHTML = `<div class="history-date">${date}</div><div class="history-title">${t.title}</div>`;
        list.appendChild(div);
    });
}
```

Function to handle selection:
```javascript
async function selectThread(id) {
    currentThreadId = id;
    loadChatHistory(); // Updates active state
    
    const res = await fetch(`/api/chats/${id}`);
    const data = await res.json();
    
    const chatWindow = document.getElementById('chat-window');
    chatWindow.innerHTML = ''; // Clear chat
    
    data.thread.messages.forEach(msg => {
        const type = msg.role === 'assistant' ? 'bot' : 'user';
        appendMessage(type, msg.content);
    });
}
```

Update `sendMessage` to pass `thread_id`:
```javascript
body: JSON.stringify({ message, thread_id: currentThreadId })
```
After successful message, call `loadChatHistory()` to update the sidebar titles/dates.

Add New Chat button listener:
```javascript
document.getElementById('new-chat-btn').addEventListener('click', () => {
    currentThreadId = null;
    document.getElementById('chat-window').innerHTML = '';
    loadChatHistory();
    appendMessage('bot', 'Welcome. I am LUME. How shall we operate today?');
});
```

Call `loadChatHistory()` on page load.
