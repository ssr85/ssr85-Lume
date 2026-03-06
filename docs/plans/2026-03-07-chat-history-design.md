# Chat History & UI Overhaul Design

## 1. Goal
Introduce a persistent chat history sidebar allowing users to recall previous contexts, and completely overhaul the existing "Bento Grid" UI into a premium 3-pane layout matching the provided screenshot design.

## 2. Architecture & Layout
The current `index.html` uses a CSS Grid (`bento-grid`). We will replace this entirely with a Flexbox/CSS Grid hybrid resulting in three main panels:
1. **Top Navigation (`header`)**: Contains the "Ask LUME" branding and a subtle hamburger menu icon for mobile (if applicable).
2. **Left Sidebar (`aside`)**: The "Chat History" panel. It will have a fixed width, contain a list of previous chat threads (grouped by time like "Yesterday", "2 days ago"), and a "New Chat" button at the top.
3. **Main Content (`main`)**: The "Agency Chat" panel. It will hold the active conversation bubbles and the input field at the bottom.

## 3. Storage & Data Model
To prevent bloating the primary business database (`storage/data.json`), we will create a dedicated storage file for conversations: `storage/chats.json`.

**Schema for `chats.json`:**
```json
{
  "current_id": 1,
  "threads": {
    "thread_1": {
      "id": "thread_1",
      "title": "Patel Proposal",
      "updated_at": "2026-03-06T15:30:00Z",
      "messages": [
         {"role": "user", "content": "Would you like to draft vilar proposal?"},
         {"role": "assistant", "content": "I've analyzed..."}
      ]
    }
  }
}
```

## 4. Backend Endpoints (FastAPI)
We need to modify `app.py` to support threading and history retrieval:
- **`GET /api/chats`**: Returns the list of all threads (id, title, updated_at) to populate the sidebar.
- **`GET /api/chats/{thread_id}`**: Returns the full message history for a specific thread to populate the main window when clicked.
- **`POST /chat`**: Modified to accept an optional `thread_id`. If omitted, a new thread is created. The LLM history context (last 6 messages) is pulled directly from the thread's stored history.

## 5. UI/UX Elements (CSS Glassmorphism)
The design relies heavily on dark mode glassmorphism and neon glows:
- **Colors**: Deep violet/blue background `#0f0f1a` (approximate).
- **Gradients**: Chat bubbles and borders will use subtle radial gradients. The bot message card uses a distinct cyan-to-purple glowing border.
- **Typography**: Refined serif for headers, clean sans-serif for chat text. 

## 6. Frontend Logic (`script.js`)
- **Initialization**: Fetch `/api/chats` on load, render sidebar items. Fetch the most recent thread or start a new one.
- **State Management**: Track `currentThreadId`. Pass it in the body of `fetch('/chat')`.
- **UI Updates**: Clicking a history item clears the chat window, fetches `/api/chats/{thread_id}`, and appends all historical messages.

## 7. Next Steps
Move to the `writing-plans` skill to break this down into atomic implementation tasks.
