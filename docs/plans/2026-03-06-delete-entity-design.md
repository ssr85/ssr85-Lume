# Delete Entity Workflow Design

## Goal
Implement a secure, UI-blocking deletion flow for clients (and projects) in LUME. The assistant will proactively ask for confirmation via a dedicated modal overlay instead of blindly executing the potentially destructive action.

## Flow
1. **User Intent:** User types "Delete client X".
2. **Backend Detection:** The Universal Agency Core (`query.py`) detects a `REQUEST_DELETE_CLIENT` action.
3. **Trigger Response:** The backend responds with a standard message AND a special JSON directive appended: `[ACTION:DELETE_MODAL:{"name":"Client X", "type":"client"}]`.
4. **Frontend Interception:** `static/app.js` runs a Regex to find `[ACTION:DELETE_MODAL:...]`. It removes this block from the visible chat output and parses the JSON.
5. **UI Blocking:** A full-screen or center modal is displayed over the dashboard. It stores "Client X" in a data attribute. The modal forces the user to manually type "Client X" into an input box.
6. **Validation:** Javascript checks `input.value === 'Client X'`. If true, the `Confirm Delete` button is enabled.
7. **Action Execution:** Clicking confirm sends a `POST` request to a new FastAPI endpoint (`/api/delete-entity`) with the entity details.
8. **Finalization:** The backend executes the deletion logic in `storage/db.py`, saving `data.json`. The frontend closes the modal, fires a visual "Deleted successfully" system message into the chat UI, and reloads the dashboard data.

## Important Implementation Details
- `db.py` must handle cascade deletion (e.g. deleting a client should theoretically clean up their projects/proposals from the JSON if they are nested, which they are in LUME).
- The modal must be hidden by default in `lume_admin_dashboard_stitch.html`.
- Requires adding the `REQUEST_DELETE_CLIENT` action to `QUERY_PROMPT`.
