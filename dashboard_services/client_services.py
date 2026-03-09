from datetime import datetime
from models.models import Client, db


class ClientServices:

    # =========================
    # Get All Clients
    # =========================
    @staticmethod
    def get_clients():
        return Client.query.order_by(Client.last_user_message_at.desc()).all()

    # =========================
    # Get Client By ID
    # =========================
    @staticmethod
    def get_client_by_id(client_id):
        return Client.query.get(client_id)

    # =========================
    # Get Client By Phone
    # =========================
    @staticmethod
    def get_client_by_phone(phone_number):
        return Client.query.filter_by(phone_number=phone_number).first()

    # =========================
    # Create Client
    # =========================
    @staticmethod
    def create_client(phone_number):

        existing = Client.query.filter_by(phone_number=phone_number).first()
        if existing:
            return existing, "هذا العميل موجود بالفعل"

        client = Client(
            phone_number=phone_number,
            created_at=datetime.utcnow()
        )

        db.session.add(client)
        db.session.commit()

        return client, "تم إضافة العميل بنجاح"

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
    # Upsert Client (for agent use)
    # =========================
    @staticmethod
    def upsert_client(phone_number, name=None, last_user_reply=None,
                      last_bot_reply=None, last_bot_reply_type=None,
                      has_purchased=False):

        now = datetime.utcnow()
        client = Client.query.filter_by(phone_number=phone_number).first()

        if not client:
            client = Client(phone_number=phone_number, created_at=now)
            db.session.add(client)
            db.session.flush()

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

        db.session.commit()
        return client.id

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
