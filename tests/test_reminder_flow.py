import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatbot.reminder import reminder_handler

def test_reminder_confirmation_success():
    print("Testing reminder confirmation: SUCCESS case")
    session = {
        "draft_reminder": "Subject: Overdue Payment\nBody: Please pay your invoice.",
        "target_client_email": "test@example.com"
    }
    
    with patch('chatbot.reminder.send_gmail', return_value=True) as mock_send:
        reply = reminder_handler("Yes, send it.", session)
        
        print(f"Reply: {reply}")
        assert "successfully" in reply
        assert "draft_reminder" not in session
        mock_send.assert_called_once_with("test@example.com", "Overdue Payment", "Please pay your invoice.")
    print("✅ Success case passed!")

def test_reminder_cancellation():
    print("Testing reminder confirmation: CANCEL case")
    session = {
        "draft_reminder": "Subject: Overdue Payment\nBody: Please pay your invoice.",
        "target_client_email": "test@example.com"
    }
    
    reply = reminder_handler("No, don't send.", session)
    print(f"Reply: {reply}")
    assert "cancelled" in reply
    assert "draft_reminder" not in session
    print("✅ Cancel case passed!")

if __name__ == "__main__":
    try:
        test_reminder_confirmation_success()
        test_reminder_cancellation()
        print("\nAll tests passed! Gmail flow confirmation is fixed.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
