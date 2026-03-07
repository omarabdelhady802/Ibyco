"""
Database service — ORM-based using shared SQLAlchemy models.
"""
from datetime import datetime
from models.database import Session
from models.models import Client, Complaint, Instalments


def _get_session():
    return Session()


def _ensure_client(session, phone_number: str) -> Client:
    """Return the client, creating the row if it doesn't exist."""
    client = session.query(Client).filter_by(phone_number=phone_number).first()
    if client:
        return client
    client = Client(phone_number=phone_number, created_at=datetime.utcnow())
    session.add(client)
    session.flush()
    return client


def upsert_client(
    phone_number: str,
    name: str = None,
    last_user_reply: str = None,
    last_bot_reply: str = None,
    last_bot_reply_type: str = None,
    has_purchased: bool = False,
) -> int:
    """Insert or update a client record. Returns the client id."""
    session = _get_session()
    now = datetime.utcnow()
    client = _ensure_client(session, phone_number)

    client.last_user_message_at = now
    client.last_bot_message_at = now
    if name:
        client.info = name
    if last_user_reply:
        client.last_user_reply = last_user_reply
    if last_bot_reply:
        client.last_bot_reply = last_bot_reply
    if last_bot_reply_type:
        client.last_bot_reply_type = last_bot_reply_type
    if has_purchased:
        client.has_purchased = True
        client.purchase_date = now

    session.commit()
    return client.id


def get_installment_rate(months: int, down_payment_pct: float = 0) -> dict:
    """Return the installment plan matching the requested months and down payment %."""
    session = _get_session()

    # Range match: lower bound exclusive, upper bound inclusive
    plan = (
        session.query(Instalments)
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
            session.query(Instalments)
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


def update_client_turn(
    phone_number: str,
    user_message: str,
    bot_response: str,
    intent: str = None,
    filters: dict = None,
    lead: dict = None,
) -> None:
    """Persist each conversation turn."""
    session = _get_session()
    client = _ensure_client(session, phone_number)
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d %H:%M")

    filters = filters or {}
    lead = lead or {}
    parts = [f"[{date_str}] intent: {intent or '-'}"]
    if filters.get("vehicle_name"):
        parts.append(f"model: {filters['vehicle_name']}")
    if filters.get("company"):
        parts.append(f"brand: {filters['company']}")
    if filters.get("max_price"):
        parts.append(f"max_price: {filters['max_price']:,}")
    if filters.get("down_payment") is not None:
        parts.append(f"down: {filters['down_payment']:,}")
    if filters.get("months"):
        parts.append(f"months: {filters['months']}")
    if filters.get("max_installment_12"):
        parts.append(f"installment: {filters['max_installment_12']:,}/mo")
    if lead.get("name"):
        parts.append(f"name: {lead['name']}")
    if lead.get("phone"):
        parts.append(f"phone: {lead['phone']}")
    short_msg = (user_message[:80] + "...") if len(user_message) > 80 else user_message
    parts.append(f'msg: "{short_msg}"')

    summary_line = " | ".join(parts)
    old_summary = client.chat_summary or ""
    new_summary = (old_summary + "\n" + summary_line).strip()
    if len(new_summary) > 4000:
        new_summary = new_summary[-4000:]

    client.chat_summary = new_summary
    client.last_user_reply = user_message[:500]
    client.last_bot_reply = bot_response[:500]
    client.last_user_message_at = now
    client.last_bot_message_at = now

    session.commit()


def save_booking(phone_number: str, name: str = None, vehicle_interest: str = None) -> int:
    """Save or update a booking/appointment request. Returns the client id."""
    session = _get_session()
    client = _ensure_client(session, phone_number)
    now = datetime.utcnow()

    client.last_user_message_at = now
    client.last_bot_message_at = now
    client.last_bot_reply_type = "booking"
    if name:
        client.info = name
    if vehicle_interest:
        client.chat_summary = f"Booking — interest: {vehicle_interest}"

    session.commit()
    return client.id


def save_complaint(phone_number: str, message_text: str) -> int:
    """Save a complaint linked to a client. Returns the complaint id."""
    session = _get_session()
    client = _ensure_client(session, phone_number)

    complaint = Complaint(
        client_id=client.id,
        message_text=message_text,
        created_at=datetime.utcnow(),
    )
    session.add(complaint)
    session.commit()
    return complaint.id
