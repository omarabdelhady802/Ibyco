from datetime import datetime
from models.models import Client, db


def _generate_summary(old_summary: str, user_message: str, bot_response: str,
                       intent: str, filters: dict, lead: dict) -> str:
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
    if len(summary) > 2000:
        summary = summary[:2000]
    return summary


class ClientServices:

    # =========================
    # Update Client
    # =========================
    @staticmethod
    def update_client(client_id, data):

        client = Client.query.get(client_id)

        if not client:
            return None, "العميل غير موجود"

        now = datetime.utcnow()

        if data.get("info"):
            client.info = data.get("info")
        if data.get("is_active") is not None:
            client.is_active = data.get("is_active") == "true"
        if data.get("has_purchased") is not None:
            was_purchased = client.has_purchased
            client.has_purchased = data.get("has_purchased") == "true"
            if client.has_purchased and not was_purchased:
                client.purchase_date = now

        db.session.commit()

        return client, "تم تعديل بيانات العميل بنجاح"

    
    # =========================
    # Save Booking
    # =========================
    @staticmethod
    def save_booking(phone_number, name=None, vehicle_interest=None):

        now = datetime.utcnow()
        client = Client.query.filter_by(phone_number=phone_number).first()

        if not client:
            client = Client(phone_number=phone_number, created_at=now)
            db.session.add(client)
            db.session.flush()

        client.last_user_message_at = now
        client.last_bot_message_at = now
        client.last_bot_reply_type = "booking"
        if name:
            client.info = name
        if vehicle_interest:
            client.chat_summary = f"Booking — interest: {vehicle_interest}"

        db.session.commit()
        return client.id

    # =========================
    # Update Client Turn (for agent)
    # =========================
    @staticmethod
    def update_client_turn(
        client,
        user_message: str,
        bot_response: str,
        intent: str = None,
        filters: dict = None,
        lead: dict = None,
    ) -> None:
        if not client:
            return

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
            new_summary = client.chat_summary or ""

        client.chat_summary = new_summary
        client.last_user_reply = user_message[:500]
        client.last_bot_reply = bot_response[:500]
        client.last_user_message_at = now
        client.last_bot_message_at = now

        db.session.commit()
