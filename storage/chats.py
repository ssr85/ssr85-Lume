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

def delete_thread(thread_id: str):
    data = load_chats()
    if thread_id in data["threads"]:
        del data["threads"][thread_id]
        save_chats(data)

def set_thread_archived(thread_id: str, archived: bool = True):
    data = load_chats()
    if thread_id in data["threads"]:
        data["threads"][thread_id]["archived"] = archived
        save_chats(data)

def get_all_threads() -> list:
    data = load_chats()
    threads = list(data["threads"].values())
    threads.sort(key=lambda x: x["updated_at"], reverse=True)
    return [{"id": t["id"], "title": t["title"], "updated_at": t["updated_at"], "archived": t.get("archived", False)} for t in threads]
