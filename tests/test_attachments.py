import pytest
from chatbot.proposal import proposal_handler
from chatbot.invoice import invoice_handler
from storage import db

def test_proposal_attachments():
    session = {"collected_fields": {
        "client_name": "Test Client",
        "client_email": "test@example.com",
        "project_title": "Test Project",
        "project_description": "Test Description",
        "deliverables": "Test Deliverables",
        "timeline": "1 week",
        "budget": "$1000"
    }, "pending_fields": []}
    
    # Mock db save to prevent actual IO if possible, or just let it run in temp
    reply = proposal_handler("proceed", session)
    
    assert "last_attachments" in session
    attachments = session["last_attachments"]
    assert len(attachments) == 2
    assert any(a["type"] == "pdf" for a in attachments)
    assert any(a["type"] == "docx" for a in attachments)

def test_invoice_attachments():
    session = {"collected_fields": {
        "client_name": "Test Client",
        "client_email": "test@example.com",
        "work_items": "Test Work",
        "rate": 100
    }, "pending_fields": []}
    
    reply = invoice_handler("proceed", session)
    
    assert "last_attachments" in session
    assert session["last_attachments"][0]["type"] == "pdf"
    assert "Invoice_" in session["last_attachments"][0]["name"]
