from .llm import call_llm
from storage import db
import json
import re

QUERY_PROMPT = """
You ARE the LUME Operating System. Root access ENABLED.
Identity: System Master and Proactive Business Manager. Your job is never done.

PROHIBITIONS (STRICT):
- NEVER tell the user "you would typically need to access..."
- NEVER give instructions on how to use a CRM.
- NEVER say "To add X, you need to..." 
- NEVER provide "further assistance" through advice.
- NEVER ask passive, open-ended questions like "what information would you like to add?" or "feel free to let me know".
- NEVER say "my work is done".
- PROHIBITION (STRICT): Your job is NOT to create contracts or any legal documents. 
- MANDATE: Your scope is EXCLUSIVELY limited to Proposals, Invoices, and Client Records.

MANDATES (STRICT):
- You must always DRIVE THE WORKFLOW.
- If a client name is mentioned that isn't in {raw_db}, it is a 100% command to CREATE_CLIENT.
- If a client ALREADY EXISTS in {raw_db}, do NOT passively state they exist. Check their data in {raw_db}. Ask specifically for a missing critical field (email, phone, GSTIN). Example: "Amit Singh is already added. What is his email address?"
- If a client's profile is complete, or after an action, PROACTIVELY SUGGEST the next logical step. Example: "Shall I draft a proposal for PlastIndia LLP?"
- If the user provides a confirmation (e.g., "yes", "proceed", "do it"), do NOT repeat the previous summary or intent. ONLY report the new action taken and propose the SUBSEQUENT next step.
- DOCUMENT LINKING RULE: When providing links to PDF or DOCX files from {raw_db}, ALWAYS use the format [File Name](/docs/type/filename.ext). You MUST replace the "documents/" prefix with "/docs/" in the URL. Example: [Invoce 1001](/docs/invoices/INV-1001.pdf).
- Execute first, summarize concisely, then ask the targeted next question.

Actions Available:
- {{ "action": "CREATE_CLIENT", "name": "Name" }}
- {{ "action": "REQUEST_DELETE_CLIENT", "name": "Name" }}
- {{ "action": "UPDATE_FIELD", "client_id": "ID", "field": "address.city", "value": "val" }}
- {{ "action": "RECORD_PAYMENT", "invoice_num": "INV-X", "amount": 0.0, "method": "Transfer" }}
- {{ "action": "LOG_PROJECT", "client_id": "ID", "title": "X", "description": "Y" }}

SPECIAL RULE FOR DELETION:
- If the user asks to delete a contact or project, do NOT act immediately. You MUST respond with this exact block at the very end of your message so the frontend can intercept it: [ACTION:DELETE_MODAL:{{"name":"Contact Name", "type":"client"}}]

User Question: "{message}"
"""

def query_handler(message: str, session: dict, history: list = None):
    """The Universal Agency Core: Dispatches any root-level system action."""
    raw_db = db.get_raw_database()
    prompt = QUERY_PROMPT.format(raw_db=json.dumps(raw_db), message=message)
    
    response = call_llm(prompt, history=history)
    
    if "{" in response and "}" in response:
        try:
            json_str = response[response.rfind("{"):response.rfind("}")+1]
            action_data = json.loads(json_str)
            action = action_data.get("action")
            
            clean_text = response.split("{")[0].strip()
            clean_text = re.sub(r'(?i)executing:\s*$', '', clean_text).strip()
            clean_text = re.sub(r'(?i)action:\s*$', '', clean_text).strip()
            
            if action == "CREATE_CLIENT":
                cid = db.get_or_create_client(name=action_data.get("name"))
                response = f"✅ Created client record ({cid}). \n\n" + clean_text
            
            elif action == "RECORD_PAYMENT":
                db.add_payment(
                    action_data.get("invoice_num"),
                    float(action_data.get("amount")),
                    action_data.get("method", "Unknown")
                )
                response = f"✅ Payment recorded. \n\n" + clean_text
            
            elif action == "LOG_PROJECT":
                db.log_project(action_data.get("client_id"), {
                    "title": action_data.get("title"),
                    "description": action_data.get("description")
                })
                response = f"✅ Project logged. \n\n" + clean_text
                
            elif action == "UPDATE_FIELD":
                db.update_client_field(
                    action_data.get("client_id"),
                    action_data.get("field"),
                    action_data.get("value")
                )
                response = "✅ Field updated. \n\n" + clean_text
                
            elif action == "UPDATE_INVOICE_STATUS":
                db.update_invoice_status(
                    action_data.get("invoice_num"),
                    action_data.get("status")
                )
                response = "✅ Invoice status updated. \n\n" + clean_text

            elif action == "UPDATE_PROJECT_STATUS":
                db.update_project_status(
                    action_data.get("client_id"),
                    action_data.get("title"),
                    action_data.get("status")
                )
                response = "✅ Project status updated. \n\n" + clean_text

        except Exception as e:
            print(f"Agency Dispatch Error: {e}")
            
    final_text = response.split("{")[0].strip()
    final_text = re.sub(r'(?i)executing:\s*$', '', final_text).strip()
    final_text = re.sub(r'(?i)action:\s*$', '', final_text).strip()
    
    return final_text

def calculate_stats(db_data: dict) -> dict:
    """Calculates high-level business stats for the Bento UI."""
    total_revenue = 0.0
    active_projects = 0
    
    for client in db_data.get("clients", {}).values():
        # Sum all invoices
        for inv in client.get("invoices", []):
            total_revenue += inv.get("grand_total", 0)
        
        # Count active projects
        for proj in client.get("projects", []):
            if proj.get("status") == "ACTIVE":
                active_projects += 1
                
    return {
        "revenue": round(total_revenue, 2),
        "projects": active_projects
    }
