# LUME Memory Management Rules

This document outlines the rules for how LUME pulls client data and updates the context window based on selected customers.

## 1. Context Injection Rules
- **Selection Trigger**: When a client is identified (via explicit selection in a future UI update or by mentioning their name in chat), the system fetches their unique `ClientID`.
- **Data Retrieval**: The system pulls the following fields from `storage/data.json`:
  - `memory`: Unstructured long-term context (e.g., "Client prefers weekend emails").
  - `preferences`: Structured key-value pairs (e.g., `{"tone": "formal"}`).
- **Injection**: This data is injected into the **System Prompt** for all subsequent messages in that session. 
- **Priority**: The LLM is instructed to treat these rules as "STRICT MANDATES" that override default behavior.

## 2. Archival & Extraction Rules
- **Trigger**: The user clicks the "Archive Chat" button in the UI.
- **Processing**:
  - The entire chat transcript is sent to a specialized LLM prompt.
  - The LLM extracts:
    - Updated contact details (Email, Phone, GSTIN, etc.)
    - New preferences (Communication style, preferred times).
    - New memory items (Specific rules mentioned during the chat).
    - A 1-sentence summary of the interaction.
- **Persistence**:
  - Scalar fields (Email, etc.) are updated in `storage/data.json` only if new values are found.
  - Preferences are merged with existing ones.
  - New memories are appended to the `memory` string with a newline.
  - The summary and thread ID are stored in the `archived_chats` array with a timestamp.

## 3. Data Privacy & Integrity
- All memory is stored locally in `storage/data.json`.
- Archived summaries allow the user to track previous interactions without cluttering the active context window.
