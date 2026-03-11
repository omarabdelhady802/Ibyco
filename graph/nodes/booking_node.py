"""
Booking Node: saves the appointment/booking request to the Booking table.
"""
from graph.state import AgentState
from dashboard_services.booking_services import BookingServices


def booking_node(state: AgentState) -> dict:
    client  = state.get("client")
    filters = state.get("filters", {})

    purpose = filters.get("vehicle_name") or filters.get("company")

    try:
        BookingServices.create_booking(client=client, purpose=purpose)
        booking_saved = True
    except Exception:
        booking_saved = False

    return {"booking_saved": booking_saved}
