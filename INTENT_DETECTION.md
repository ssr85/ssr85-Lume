# Intent Detection

## Overview

Every message the freelancer sends is first classified into one of four intents before any processing begins. This classification step is called **Intent Detection**. It is handled by a centralized LLM wrapper (`chatbot/llm.py`) with a keyword fallback mechanism.

> [!NOTE]
> All intent detection and subsequent logic now utilize the **Client Memory** and **Preferences** injected into the System Prompt, ensuring that even classification can be context-aware if necessary.

---

## Intent Categories

| Intent | Trigger Description | Example Messages |
|---|---|---|
| `PROPOSAL` | User wants to create a new project proposal | "I need a proposal for...", "Write a proposal for my new client" |
| `INVOICE` | User wants to generate an invoice | "Create an invoice for...", "Bill TechStart for 12 hours" |
| `REMINDER` | User wants to send a payment reminder | "Send a reminder to...", "Follow up on the unpaid invoice" |
| `QUERY` | User is asking about stored data | "Show all unpaid invoices", "Mark invoice #1042 as paid" |

---

## Primary Method: LLM Classification

The user message is sent to the LLM via `call_llm()` in `chatbot/llm.py`. This handles natural language variations reliably.

```python
INTENT_PROMPT = """
You are an intent classifier for a freelancer admin chatbot.
Classify the following user message into exactly one of these intents:
- PROPOSAL: User wants to generate a project proposal
- INVOICE: User wants to create an invoice
- REMINDER: User wants to send a payment reminder to a client
- QUERY: User is asking about stored data or invoice status

Respond with only the intent label. No explanation.

User message: "{message}"
"""
```

---

## Fallback: Keyword Matching

If the LLM is unavailable or returns an unexpected response, keyword matching is used:

```python
INTENT_KEYWORDS = {
    "PROPOSAL": ["proposal", "propose", "pitch", "brief", "write a proposal"],
    "INVOICE": ["invoice", "bill", "billing", "hours", "rate", "charge"],
    "REMINDER": ["remind", "reminder", "overdue", "follow up", "hasn't paid", "still unpaid"],
    "QUERY": ["show", "list", "unpaid", "status", "mark as paid", "check"],
}

def keyword_detect(message: str) -> str:
    msg = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return intent
    return "UNKNOWN"
```

---

## Routing Logic

Once the intent is detected, the message is routed to the appropriate module:

```python
def route(intent: str, message: str, session: dict):
    if intent == "PROPOSAL":
        return proposal_handler(message, session)
    elif intent == "INVOICE":
        return invoice_handler(message, session)
    elif intent == "REMINDER":
        return reminder_handler(message, session)
    elif intent == "QUERY":
        return query_handler(message, session)
    else:
        return (
            "I'm not sure what you need. You can ask me to write a proposal, "
            "create an invoice, send a payment reminder, or check invoice status."
        )
```

---

## Multi-Turn Context

Once an intent is established, the session state preserves it across follow-up messages until the task is complete. The bot does not re-classify mid-flow.

```python
if session.get("intent"):
    return route(session["intent"], message, session)
else:
    intent = detect_intent(message)
    session["intent"] = intent
    return route(intent, message, session)
```

---

## Resetting Intent

The session intent is cleared when:
- A task is fully completed (proposal saved, invoice downloaded, reminder sent)
- The freelancer sends a message that clearly starts a new, different task
- The freelancer explicitly says "cancel", "start over", or "never mind"
