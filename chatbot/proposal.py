import os
from .llm import call_llm
from storage import db
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PROPOSAL_PROMPT = """
You are a professional proposal writer. Generate a complete, polished project proposal.
The tone should match the project type (e.g., creative and expressive for design, clear and structured for technical).

User Details:
- Freelancer Name: {freelancer_name}
- Client Name: {client_name}
- Project Title: {project_title}
- Description: {project_description}
- Deliverables: {deliverables}
- Timeline: {timeline}
- Budget: {budget}
- Background: {freelancer_background}

The proposal must have these sections:
1. Introduction
2. Project Understanding
3. Proposed Approach
4. Deliverables
5. Timeline
6. Pricing
7. Terms
8. Closing

Do not use placeholders like [Insert Name]. Use the real data.
Respond with the full markdown content of the proposal.
"""

EDIT_PROMPT = """
Update the following proposal based on the user's instructions.
Keep the existing structure and data, but apply the changes requested.

Original Proposal:
{content}

User Instructions:
"{instruction}"

Respond with ONLY the full updated markdown content.
"""

def proposal_handler(message: str, session: dict):
    """Manages the proposal generation flow and editing loop."""
    from .intent import extract_fields
    
    # Extract fields if not already in session
    extracted = extract_fields(message, "PROPOSAL")
    for key, val in extracted.items():
        if val and not session["collected_fields"].get(key):
            session["collected_fields"][key] = val
            
    # Required fields check
    required = ["client_name", "project_title", "project_description", "deliverables", "timeline"]
    missing = [f for f in required if not session["collected_fields"].get(f)]
    
    if missing:
        field_labels = {
            "client_name": "client name",
            "project_title": "project title",
            "project_description": "brief project description",
            "deliverables": "main deliverables",
            "timeline": "expected timeline"
        }
        return f"I'll help you with that proposal! To get started, could you tell me the **{field_labels[missing[0]]}**?"

    # If we have basic info but no email for a new client
    client_name = session["collected_fields"]["client_name"]
    client_id = db.find_client_by_name_and_email(client_name)
    
    if not client_id and not session["collected_fields"].get("client_email"):
        session["pending_fields"] = ["client_email"]
        return f"Got it. I don't see **{client_name}** in your records. What's their email address so I can set them up?"

    if not client_id and session["collected_fields"].get("client_email"):
        client_id = db.get_or_create_client(
            name=client_name, 
            email=session["collected_fields"]["client_email"]
        )

    # All data ready, generate or edit
    freelancer_name = os.getenv("FREELANCER_NAME", "your assistant")
    
    if session.get("draft_content") and not session.get("intent_reset"):
        # This is an edit instruction
        new_content = call_llm(EDIT_PROMPT.format(
            content=session["draft_content"],
            instruction=message
        ))
        session["draft_content"] = new_content
    else:
        # Initial generation
        prompt = PROPOSAL_PROMPT.format(
            freelancer_name=freelancer_name,
            **session["collected_fields"],
            freelancer_background=session["collected_fields"].get("freelancer_background", "Highly experienced professional")
        )
        session["draft_content"] = call_llm(prompt)
        session["intent_reset"] = False

    # Save and return preview
    # Initial generation or edit completed
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    client_slug = client_name.lower().replace(" ", "_")
    pdf_filename = f"proposal_{client_slug}_{timestamp}.pdf"
    docx_filename = f"proposal_{client_slug}_{timestamp}.docx"
    
    pdf_path = f"documents/proposals/{pdf_filename}"
    docx_path = f"documents/proposals/{docx_filename}"
    
    from documents.pdf_generator import generate_proposal_pdf
    from documents.docx_generator import generate_proposal_docx
    
    generate_proposal_pdf(session["draft_content"], pdf_path)
    generate_proposal_docx(session["draft_content"], docx_path)
    
    db.save_proposal(
        client_id=client_id,
        proposal_metadata=session["collected_fields"],
        content=session["draft_content"],
        file_path=pdf_path
    )
    
    # Return preview with real links (simulated for now with /docs path)
    return (
        f"### Proposal Preview\n\n{session['draft_content']}\n\n"
        "--- \n"
        "**Would you like to refine anything in the draft?** (e.g., 'Make it more technical', 'Add 20% upfront payment term')\n\n"
        f"Otherwise, you can download it as [**PDF**](/docs/proposals/{pdf_filename}) or [**Word**](/docs/proposals/{docx_filename})."
    )
