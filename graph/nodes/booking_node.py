"""
Booking Node: saves the appointment/booking request to the Booking table.
"""
from graph.state import AgentState
from dashboard_services.booking_services import BookingServices


def booking_node(state: AgentState) -> dict:
    lead = state.get("lead", {})
    client = state.get("client")

    date    = lead.get("appointment_date")
    purpose = lead.get("booking_purpose")

    name = lead.get("name")

    # Don't save yet if we're missing key info — let LLM ask first
    if not client or not date or not name:
        return {"booking_saved": False}

    try:
        BookingServices.create_booking(client=client, purpose=purpose, date=date)
        booking_saved = True
    except Exception:
        booking_saved = False

    return {"booking_saved": booking_saved}
