"""
Complaint Node: saves the complaint to the SQLite DB and sets a flag
so the response_node can generate an appropriate acknowledgement.
"""
from graph.state import AgentState
from dashboard_services.complaint_services import ComplaintServices


def complaint_node(state: AgentState) -> dict:
    client  = state.get("client")
    message = state.get("current_message", "")

    try:
        ComplaintServices.create_complaint(client=client, message_text=message)
        complaint_saved = True
    except Exception:
        complaint_saved = False

    return {"complaint_saved": complaint_saved}
