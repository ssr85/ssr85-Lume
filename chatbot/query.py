from .llm import call_llm
from storage import db
import json

QUERY_PROMPT = """
You ARE the LUME Operating System. You have full root access to the database.
You are the System Master. Do not suggest; EXECUTE.

Current Database State:
{raw_db}

Actions Available (Return as JSON at end of message):
- {{ "action": "CREATE_CLIENT", "name": "Name" }}
- {{ "action": "UPDATE_FIELD", "client_id": "ID", "field": "address.city", "value": "val" }}
- {{ "action": "RECORD_PAYMENT", "invoice_num": "INV-X", "amount": 0.0, "method": "Transfer" }}
- {{ "action": "LOG_PROJECT", "client_id": "ID", "title": "X", "description": "Y" }}

Analytics & Agency Use Cases:
1. Financial Health: Calculate total revenue, pending balances, and average project value.
2. Client Insights: Identify top clients by value, geographical revenue distribution, and payment punctuality.
3. Workflow Management: Count active vs completed projects, overdue invoices, and conversion ratios.
4. Proactive Operations: Mentioning a client should trigger an immediate update or a workflow suggestion.

Instructions:
- If a mutation is requested, include the JSON action.
- If analysis is requested, process the `raw_db` precisely and output a professional summary.
- Be authoritative and proactive.

User Question: "{message}"
"""

def query_handler(message: str, session: dict):
    """The Universal Agency Core: Dispatches any root-level system action."""
    raw_db = db.get_raw_database()
    prompt = QUERY_PROMPT.format(raw_db=json.dumps(raw_db), message=message)
    response = call_llm(prompt)
    
    if "{" in response and "}" in response:
        try:
            json_str = response[response.rfind("{"):response.rfind("}")+1]
            action_data = json.loads(json_str)
            action = action_data.get("action")
            
            if action == "CREATE_CLIENT":
                cid = db.get_or_create_client(name=action_data.get("name"))
                response = f"✅ Created client record ({cid}). \n\n" + response.split("{")[0]
            
            elif action == "RECORD_PAYMENT":
                db.add_payment(
                    action_data.get("invoice_num"),
                    float(action_data.get("amount")),
                    action_data.get("method", "Unknown")
                )
                response = f"✅ Payment recorded. \n\n" + response.split("{")[0]
            
            elif action == "LOG_PROJECT":
                db.log_project(action_data.get("client_id"), {
                    "title": action_data.get("title"),
                    "description": action_data.get("description")
                })
                response = f"✅ Project logged. \n\n" + response.split("{")[0]
                
            elif action == "UPDATE_FIELD":
                db.update_client_field(
                    action_data.get("client_id"),
                    action_data.get("field"),
                    action_data.get("value")
                )
                response = "✅ Field updated. \n\n" + response.split("{")[0]
                
            elif action == "UPDATE_INVOICE_STATUS":
                db.update_invoice_status(
                    action_data.get("invoice_num"),
                    action_data.get("status")
                )
                response = "✅ Invoice status updated. \n\n" + response.split("{")[0]

            elif action == "UPDATE_PROJECT_STATUS":
                db.update_project_status(
                    action_data.get("client_id"),
                    action_data.get("title"),
                    action_data.get("status")
                )
                response = "✅ Project status updated. \n\n" + response.split("{")[0]

        except Exception as e:
            print(f"Agency Dispatch Error: {e}")
            
    return response.split("{")[0].strip()
