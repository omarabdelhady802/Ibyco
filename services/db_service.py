"""
Database service — delegates to dashboard services for client/complaint ops,
keeps agent-specific logic (installment lookup, LLM summary, turn tracking).
"""
from datetime import datetime
from models.models import db, Instalments
from dashboard_services.client_services import ClientServices
from dashboard_services.complaint_services import ComplaintServices


def upsert_client(
    phone_number: str,
    name: str = None,
    last_user_reply: str = None,
    last_bot_reply: str = None,
    last_bot_reply_type: str = None,
    has_purchased: bool = False,
) -> int:
    """Insert or update a client record. Returns the client id."""
    return ClientServices.upsert_client(
        phone_number, name, last_user_reply,
        last_bot_reply, last_bot_reply_type, has_purchased
    )


def get_installment_rate(months: int, down_payment_pct: float = 0) -> dict:
    """Return the installment plan matching the requested months and down payment %."""
    # Range match: lower bound exclusive, upper bound inclusive
    plan = (
        Instalments.query
        .filter(
            Instalments.min_down_payment <= down_payment_pct,
            Instalments.max_down_payment > down_payment_pct,
            Instalments.min_months < months,
            Instalments.max_months >= months,
        )
        .order_by(Instalments.max_months.asc())
        .first()
    )

    if not plan:
        # Fallback: widest plan for this down payment tier
        plan = (
            Instalments.query
            .filter(
                Instalments.min_down_payment <= down_payment_pct,
                Instalments.max_down_payment > down_payment_pct,
            )
            .order_by(Instalments.max_months.desc())
            .first()
        )

    if not plan:
        return {}

    return {
        "percentage": plan.percentage,
        "percentage_per_month": plan.percentage_per_month,
        "max_months": plan.max_months,
    }


def _generate_summary(old_summary: str, user_message: str, bot_response: str,
                       intent: str, filters: dict, lead: dict) -> str:
    """Use the LLM to produce a concise updated client summary."""
    from llm.gemini import get_gemini

    filter_parts = []
    if filters.get("vehicle_name"):
        filter_parts.append(f"vehicle: {filters['vehicle_name']}")
    if filters.get("company"):
        filter_parts.append(f"brand: {filters['company']}")
    if filters.get("max_price"):
        filter_parts.append(f"max_price: {filters['max_price']:,}")
    if filters.get("min_price"):
        filter_parts.append(f"min_price: {filters['min_price']:,}")
    if filters.get("down_payment") is not None:
        filter_parts.append(f"down_payment: {filters['down_payment']:,}")
    if filters.get("months"):
        filter_parts.append(f"months: {filters['months']}")
    filter_str = ", ".join(filter_parts) if filter_parts else "none"

    lead_parts = []
    if lead.get("name"):
        lead_parts.append(f"name: {lead['name']}")
    if lead.get("phone"):
        lead_parts.append(f"phone: {lead['phone']}")
    lead_str = ", ".join(lead_parts) if lead_parts else "none"

    prompt = f"""You are a CRM assistant. Update the client summary below with the latest conversation turn.

EXISTING SUMMARY:
{old_summary or '(new client — no history yet)'}

LATEST TURN:
- Intent: {intent or 'unknown'}
- Filters: {filter_str}
- Lead info: {lead_str}
- Customer said: "{user_message[:300]}"
- Bot replied: "{bot_response[:300]}"

RULES:
1. Merge the new turn into the existing summary — do NOT just append.
2. Keep it concise (max 500 characters). Use bullet points.
3. Preserve important facts: client name, phone, vehicles of interest, price range, installment preferences, complaints, bookings.
4. Drop outdated or redundant details.
5. Write in English.
6. Output ONLY the updated summary, nothing else."""

    llm = get_gemini()
    result = llm.invoke(prompt)
    summary = result.content.strip()
    # Safety cap
    if len(summary) > 2000:
        summary = summary[:2000]
    return summary


def update_client_turn(
    phone_number: str,
    user_message: str,
    bot_response: str,
    intent: str = None,
    filters: dict = None,
    lead: dict = None,
) -> None:
    """Persist each conversation turn with an LLM-generated summary."""
    # Ensure client exists via dashboard service
    client = ClientServices.get_client_by_phone(phone_number)
    if not client:
        ClientServices.create_client(phone_number)
        client = ClientServices.get_client_by_phone(phone_number)

    now = datetime.utcnow()
    filters = filters or {}
    lead = lead or {}

    try:
        new_summary = _generate_summary(
            old_summary=client.chat_summary or "",
            user_message=user_message,
            bot_response=bot_response,
            intent=intent,
            filters=filters,
            lead=lead,
        )
    except Exception:
        # Fallback: keep existing summary if LLM fails
        new_summary = client.chat_summary or ""

    client.chat_summary = new_summary
    client.last_user_reply = user_message[:500]
    client.last_bot_reply = bot_response[:500]
    client.last_user_message_at = now
    client.last_bot_message_at = now

    db.session.commit()


def save_booking(phone_number: str, name: str = None, vehicle_interest: str = None) -> int:
    """Save or update a booking/appointment request. Returns the client id."""
    return ClientServices.save_booking(phone_number, name, vehicle_interest)


def save_complaint(phone_number: str, message_text: str) -> int:
    """Save a complaint linked to a client. Returns the complaint id."""
    return ComplaintServices.create_complaint(phone_number, message_text)
