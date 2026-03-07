from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from chatbot.intent import detect_intent
from chatbot.proposal import proposal_handler
from chatbot.invoice import invoice_handler
from chatbot.reminder import reminder_handler
from chatbot.query import query_handler, calculate_stats
from chatbot.gmail_sender import send_gmail
from storage import db, chats

app = FastAPI(title="LUME - Freelancer Admin Assistant")

# Session state simulation (per user, in-memory for MVP)
sessions = {}

# Ensure required directories exist
os.makedirs("storage", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("documents/proposals", exist_ok=True)
os.makedirs("documents/invoices", exist_ok=True)

# Mount statics and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/docs", StaticFiles(directory="documents"), name="documents")
app.mount("/documents", StaticFiles(directory="documents"), name="documents_compat")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "ok", "app": "LUME"}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    thread_id = data.get("thread_id")
    
    if not thread_id:
        title = " ".join(message.split()[:3]) + "..."
        thread_id = chats.create_thread(title)
        
    chats.append_message(thread_id, "user", message)
    
    user_id = "default_user" # Simplified for MVP
    
    if user_id not in sessions:
        sessions[user_id] = {"collected_fields": {}, "pending_fields": [], "current_intent": None}
    
    session = sessions[user_id]
    session["thread_id"] = thread_id
    
    # Get previous chat history for LLM context, max last 50 messages for better window
    thread = chats.get_thread(thread_id)
    history = thread.get("messages", [])[:-1] # excluding the recently added user message
    if len(history) > 50:
        history = history[-50:]
    
    # Intent classification
    intent = detect_intent(message, history=history, current_intent=session.get("current_intent"))
    if intent != "UNKNOWN" and intent != session["current_intent"]:
        session["current_intent"] = intent
        session["intent_reset"] = True # Flag to trigger new gen vs edit
    
    # Route to handler - passing history for context-aware responses
    if session["current_intent"] == "PROPOSAL":
        reply = proposal_handler(message, session, history=history)
    elif session["current_intent"] == "INVOICE":
        reply = invoice_handler(message, session, history=history)
    elif session["current_intent"] == "REMINDER":
        reply = reminder_handler(message, session, history=history)
    else:
        reply = query_handler(message, session, history=history)
    
    # Save Assistant Reply to History
    chats.append_message(thread_id, "assistant", reply)
    
    # Always send fresh stats for the Bento UI
    raw_db = db.get_raw_database()
    stats = calculate_stats(raw_db)
        
    response_data = {
        "reply": reply, 
        "stats": stats, 
        "thread_id": thread_id,
        "attachments": session.get("last_attachments", [])
    }
    
    # Clear attachments after sending
    if "last_attachments" in session:
        del session["last_attachments"]
        
    return response_data

class DeleteRequest(BaseModel):
    target_name: str
    entity_type: str

@app.post("/api/delete-entity")
async def delete_entity(req: DeleteRequest):
    if req.entity_type == "client":
        success = db.delete_client_by_name(req.target_name)
        if success:
            return {"status": "success", "message": f"Client {req.target_name} deleted."}
        else:
            return {"status": "error", "message": f"Client {req.target_name} not found."}
    return {"status": "error", "message": "Unknown entity type."}

@app.get("/api/chats")
async def get_chats():
    return {"status": "success", "threads": chats.get_all_threads()}

@app.get("/api/chats/{thread_id}")
async def get_chat_thread(thread_id: str):
    thread = chats.get_thread(thread_id)
    if thread:
        return {"status": "success", "thread": thread}
    return {"status": "error", "message": "Thread not found"}

@app.delete("/api/chats/{thread_id}")
async def delete_chat_thread(thread_id: str):
    chats.delete_thread(thread_id)
    return {"status": "success"}

class SendDocumentRequest(BaseModel):
    file_url: str

@app.post("/api/send-document")
async def send_document(req: SendDocumentRequest):
    # Convert /docs/proposals/foo.pdf to documents/proposals/foo.pdf
    if req.file_url.startswith("/docs/"):
        file_path = "documents/" + req.file_url[6:]
    else:
        return {"status": "error", "message": "Invalid file URL"}

    # Find the client associated with this file_path
    db_data = db.get_raw_database()
    target_client = None
    target_proposal = None

    for client in db_data["clients"].values():
        # Check Proposals (PDF or DOCX)
        for prop in client.get("proposals", []):
            if prop.get("pdf_path") == file_path or prop.get("docx_path") == file_path:
                target_client = client
                break
        if target_client: break
        
        # Check Invoices
        for inv in client.get("invoices", []):
            if inv.get("file_path") == file_path:
                target_client = client
                break
        if target_client: break

    if not target_client or not target_client.get("email"):
        return {"status": "error", "message": "Client or client email not found for this document"}

    # Use gmail_sender to send the email with actual attachment
    subject = f"Document from LUME: {os.path.basename(file_path)}"
    body = f"Hello {target_client['name']},\n\nPlease find the discussed document attached.\n\nRegards,\nLUME AI"
    
    success = send_gmail(target_client["email"], subject, body, attachment_path=file_path)
    
    if success:
        return {"status": "success", "message": f"Document sent to {target_client['email']}"}
    else:
        return {"status": "error", "message": "Failed to send email. Check system logs/credentials."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
