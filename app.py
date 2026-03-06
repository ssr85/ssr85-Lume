from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from chatbot.intent import detect_intent
from chatbot.proposal import proposal_handler
from chatbot.invoice import invoice_handler
from chatbot.reminder import reminder_handler
from chatbot.query import query_handler

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
    user_id = "default_user" # Simplified for MVP
    
    if user_id not in sessions:
        sessions[user_id] = {"collected_fields": {}, "pending_fields": [], "current_intent": None}
    
    session = sessions[user_id]
    
    # Intent classification
    intent = detect_intent(message)
    if intent != "UNKNOWN" and intent != session["current_intent"]:
        session["current_intent"] = intent
        session["intent_reset"] = True # Flag to trigger new gen vs edit
        
    # Route to handler
    if session["current_intent"] == "PROPOSAL":
        reply = proposal_handler(message, session)
    elif session["current_intent"] == "INVOICE":
        reply = invoice_handler(message, session)
    elif session["current_intent"] == "REMINDER":
        reply = reminder_handler(message, session)
    else:
        reply = query_handler(message, session)
        
    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
