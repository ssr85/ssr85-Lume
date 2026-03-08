import json
from datetime import datetime
from storage import db, chats
from pydantic import BaseModel

MEMORY_EXTRACTION_PROMPT = """
You are an AI assistant analyzing a conversation between a freelancer (the AI) and their client.
Your goal is to extract any updated contact information, define the client's preferences, and note any unstructured memory/rules of engagement.
You must also provide a concise 1-sentence summary of the interaction.

Output JSON exactly matching this format:
{
  "email": "extracted email or empty string",
  "phone": "extracted phone or empty string",
  "company": "extracted company or empty string",
  "city": "extracted city or empty string",
  "country": "extracted country or empty string",
  "gstin": "extracted gstin or empty string",
  "preferences": {
    "key": "value" // e.g., "communication_style": "formal", "preferred_contact_time": "morning"
  },
  "memory": "Any new, persistent rules of engagement or context to remember for this client. If none, leave empty.",
  "summary": "1-sentence summary of what happened in this chat."
}
"""

def archive_chat(thread_id: str, client_id: str) -> bool:
    """
    Archives a chat thread, extracts client info/preferences via LLM, and updates the db.
    Returns True on success, False otherwise.
    """
    client = db.get_client(client_id)
    if not client:
        print(f"Error: Client {client_id} not found.")
        return False
        
    thread = chats.get_thread(thread_id)
    if not thread or not thread.get("messages"):
        print(f"Error: Thread {thread_id} not found or empty.")
        return False
        
    # Format transcript
    transcript = ""
    for msg in thread["messages"]:
        role = "Freelancer (AI)" if msg["role"] == "assistant" else "Client (User)"
        transcript += f"{role}: {msg['content']}\n\n"
        
    # Call LLM for extraction
    prompt = f"{MEMORY_EXTRACTION_PROMPT}\n\nTRANSCRIPT:\n{transcript}"
    
    try:
        from chatbot.llm import call_llm
        response_text = call_llm(
            prompt=prompt,
            json_mode=True,
            system_message="You are a helpful assistant that only outputs JSON."
        )
        
        extracted_data = json.loads(response_text)
        
        # Update scalar fields if provided
        scalar_fields = ["email", "phone", "company", "gstin"]
        for field in scalar_fields:
            if extracted_data.get(field):
                db.update_client_field(client_id, field, extracted_data[field])
                
        # Update address if provided
        address = client.get("address", {})
        address_updated = False
        if extracted_data.get("city"):
            address["city"] = extracted_data["city"]
            address_updated = True
        if extracted_data.get("country"):
            address["country"] = extracted_data["country"]
            address_updated = True
            
        if address_updated:
            db.update_client_field(client_id, "address", address)
            
        # Merge preferences
        current_prefs = client.get("preferences", {})
        new_prefs = extracted_data.get("preferences", {})
        if new_prefs:
            current_prefs.update(new_prefs)
            db.update_client_field(client_id, "preferences", current_prefs)
            
        # Append memory
        current_memory = client.get("memory", "")
        new_memory = extracted_data.get("memory", "")
        if new_memory:
            updated_memory = current_memory + "\n" + new_memory if current_memory else new_memory
            db.update_client_field(client_id, "memory", updated_memory.strip())
            
        # Append to archived_chats
        archived_entry = {
            "date": datetime.now().isoformat(),
            "summary": extracted_data.get("summary", "Chat archived."),
            "thread_id": thread_id
        }
        
        # We need to load db, update, and save manually for array append
        db_data = db.load_db()
        if client_id in db_data["clients"]:
            db_data["clients"][client_id].setdefault("archived_chats", []).append(archived_entry)
            db.save_db(db_data)
        
        # Mark thread as archived in chat storage
        chats.set_thread_archived(thread_id)
        
        return True, extracted_data
        
    except Exception as e:
        print(f"Error archiving chat: {e}")
        return False, None
