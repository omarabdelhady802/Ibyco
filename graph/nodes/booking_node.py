"""
Booking Node: saves the appointment/booking request to the Booking table.
Uses the client (already identified by WhatsApp number) — no need for name/phone from lead.
"""
from graph.state import AgentState
from dashboard_services.booking_services import BookingServices
from notified_center.Email_sender import EmailClient
email_client = EmailClient()
import traceback

def booking_node(state: AgentState) -> dict:
    lead = state.get("lead", {})
    client = state.get("client")

    date    = lead.get("appointment_date")
    purpose = lead.get("booking_purpose")

    print(f"\n── Debug: booking_node ─────────────────────")
    print(f"  Client: {client} (id={client.id if client else None}, phone={client.phone_number if client else None})")
    print(f"  Date: {date}")
    print(f"  Purpose: {purpose}")
    print(f"  Lead: {lead}")
    print(f"───────────────────────────────────────────")

    # Don't save yet if we're missing the date — let LLM ask first
    if not client or not date:
        return {"booking_saved": False}

    try:
        booking_id = BookingServices.create_booking(client=client, purpose=purpose, date=date)
        print(f"  ✓ Booking saved! ID={booking_id}")
        booking_saved = True
    except Exception as e:
        print(f"  ✗ Booking save FAILED: {e}")
        import traceback
        traceback.print_exc()
        booking_saved = False
        email_client.send_email(
            subject="Booking Save Failed in booking_node file",
            body=f"An error occurred while saving a booking:\n\nClient: {client}\nDate: {date}\nPurpose: {purpose}\n\nError:\n{traceback.format_exc()}"
        )

    return {"booking_saved": booking_saved}
