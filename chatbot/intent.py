from .llm import call_llm

INTENT_PROMPT = """
You are an intent classifier for LUME, a freelancer's admin assistant.
Classify the following user message into exactly one of these intents:
- PROPOSAL: User wants to generate a project proposal.
- INVOICE: User wants to create/generate an invoice.
- REMINDER: User wants to send a payment reminder to a client.
- QUERY: User is asking about stored data (unpaid invoices, client info, marking as paid).

Respond with ONLY the intent label.

User message: "{message}"
"""

EXTRACT_PROMPT = """
Extract fields from the user message for a {intent} task.
Return as a JSON object. Use null if not found.

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

def detect_intent(message: str) -> str:
    """Detects user intent via LLM with keyword fallback."""
    msg = message.lower()
    
    # Aggressive Agency Routing: Force into Agency Core if mutation keywords OR potential names are detected
    mutation_keywords = ["create", "add", "set", "update", "total", "calculate", "new", "record"]
    if any(kw in msg for kw in mutation_keywords):
        return "QUERY"
        
    # Heuristic for Names (Capitalized words in a short sentence)
    words = message.split()
    if len(words) < 15 and any(w[0].isupper() for w in words[1:]): # Basic name detection
         return "QUERY"

    # Try LLM
    intent = call_llm(INTENT_PROMPT.format(message=message))
    if intent and intent.strip() in ["PROPOSAL", "INVOICE", "REMINDER", "QUERY"]:
        return intent.strip()
    
    # Fallback to keywords
    for label, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return label
    return "UNKNOWN"

def extract_fields(message: str, intent: str) -> dict:
    """Extracts relevant fields from a message based on intent."""
    prompt = EXTRACT_PROMPT.format(message=message, intent=intent)
    result = call_llm(prompt, json_mode=True)
    try:
        import json
        return json.loads(result) if result else {}
    except:
        return {}
