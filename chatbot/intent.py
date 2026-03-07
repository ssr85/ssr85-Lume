from .llm import call_llm

INTENT_PROMPT = """
You are an intent classifier for LUME, a freelancer's admin assistant.
Classify the following user message into exactly one of these intents:
- PROPOSAL: User wants to draft, create, or generate a NEW project proposal.
- INVOICE: User wants to draft, create, or generate a NEW invoice.
- REMINDER: User wants to draft or generate a payment reminder.
- QUERY: User wants to EMAIL/SEND an EXISTING document (like a proposal or invoice), ask about stored data, or update records.

Respond with ONLY the intent label.

User message: "{message}"
"""

EXTRACT_PROMPT = """
Extract fields from the user message for a {intent} task.
Return as a JSON object. Use null if not found.

Be proactive: if a piece of information can serve multiple fields (e.g. "Logo Design" is both a title and a description), use it for both.

Fields to extract:
- For PROPOSAL: client_name, project_title, project_description, deliverables, timeline, budget, freelancer_background
- For INVOICE: client_name, project_name, work_items, hours, rate, gstin, phone_number
- For REMINDER: client_name, invoice_number

Message: "{message}"
"""

INTENT_KEYWORDS = {
    "PROPOSAL": ["proposal", "propose", "pitch", "brief"],
    "INVOICE": ["invoice", "bill", "billing", "charge"],
    "REMINDER": ["remind", "reminder", "overdue", "follow up", "hasn't paid"],
    "QUERY": ["create", "add", "set", "update", "change", "show", "list", "unpaid", "status", "mark as paid", "total", "calculate", "how much"],
}

def detect_intent(message: str, history: list = None, current_intent: str = None) -> str:
    """Detects user intent via LLM with keyword fallback."""
    msg = message.lower()
    
    # If they are explicitly asking to send a document that already exists
    if "send" in msg and any(doc in msg for doc in ["proposal", "invoice", "document", "file", "pdf", "docx", "email"]):
        return "QUERY"
        
    in_flow = current_intent in ["PROPOSAL", "INVOICE", "REMINDER"]
    
    if not in_flow:
        # Avoid aggressive QUERY routing if the user is explicitly trying to generate documents
        if not any(doc in msg for doc in ["invoice", "bill", "proposal", "pitch"]):
            # Aggressive Agency Routing: Force into Agency Core if mutation keywords OR potential names are detected
            mutation_keywords = ["create", "add", "set", "update", "total", "calculate", "new", "record", "email"]
            if any(kw in msg for kw in mutation_keywords):
                return "QUERY"
                
            # Heuristic for Names (Capitalized words in a short sentence)
            words = message.split()
            if len(words) < 15 and any(w[0].isupper() for w in words[1:]): # Basic name detection
                 return "QUERY"

    # Try LLM
    intent = call_llm(INTENT_PROMPT.format(message=message), history=history)
    if intent and intent.strip() in ["PROPOSAL", "INVOICE", "REMINDER", "QUERY"]:
        return intent.strip()
    
    # Fallback to keywords
    for label, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return label
    return "UNKNOWN"

def extract_fields(message: str, intent: str, history: list = None) -> dict:
    """Extracts relevant fields from a message based on intent."""
    prompt = EXTRACT_PROMPT.format(message=message, intent=intent)
    result = call_llm(prompt, json_mode=True, history=history)
    try:
        import json
        return json.loads(result) if result else {}
    except:
        return {}
