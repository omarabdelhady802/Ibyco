"""
Booking Node: saves the appointment/booking request to the Booking table.
"""
from graph.state import AgentState
from dashboard_services.booking_services import BookingServices


def booking_node(state: AgentState) -> dict:
    lead = state.get("lead", {})

    name    = lead.get("name")
    phone   = lead.get("phone")
    date    = lead.get("appointment_date")
    purpose = lead.get("booking_purpose")

    # Require name, phone, and date before saving
    if not (name and phone and date):
        return {"booking_saved": False}

    client = state.get("client")
    try:
        BookingServices.create_booking(client=client, purpose=purpose, date=date)
        booking_saved = True
    except Exception:
        booking_saved = False

    return {"booking_saved": booking_saved}
