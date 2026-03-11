from datetime import datetime, timezone
from models.models import Booking, Client, db


class BookingServices:

    # =========================
    # Get All Bookings
    # =========================
    @staticmethod
    def get_bookings():
        return Booking.query.order_by(Booking.created_at.desc()).all()

    # =========================
    # Get Bookings By Phone
    # =========================
    @staticmethod
    def get_bookings_by_phone(phone=None):
        if not phone:
            return Booking.query.order_by(Booking.created_at.desc()).all()
        client = Client.query.filter_by(phone_number=phone).first()
        if not client:
            return []
        return Booking.query.filter_by(client_id=client.id).order_by(Booking.created_at.desc()).all()

    # =========================
    # Get Booking By ID
    # =========================
    @staticmethod
    def get_booking_by_id(booking_id):
        return Booking.query.get(booking_id)

    # =========================
    # Create Booking (for agent)
    # =========================
    @staticmethod
    def create_booking(client, purpose=None):
        booking = Booking(
            client_id=client.id if client else None,
            purpose=purpose,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(booking)
        db.session.commit()

        return booking.id

    # =========================
    # Update Booking Status
    # =========================
    @staticmethod
    def update_status(booking_id, status):
        booking = Booking.query.get(booking_id)

        if not booking:
            return None, "الحجز غير موجود"

        booking.status = status
        db.session.commit()

        return booking, "تم تحديث الحجز بنجاح"

    # =========================
    # Update Booking + Client (dashboard)
    # =========================
    @staticmethod
    def update_booking_and_client(booking_id, form):
        booking = Booking.query.get(booking_id)

        if not booking:
            return None, "الحجز غير موجود"

        booking.status  = form.get("status", booking.status)
        booking.purpose = form.get("purpose", booking.purpose)
        booking.date    = form.get("date", booking.date)

        client = booking.client
        if client:
            if form.get("info"):
                client.info = form.get("info")
            if form.get("has_purchased") is not None:
                from datetime import datetime, timezone
                client.has_purchased = form.get("has_purchased") == "true"
                if client.has_purchased:
                    client.purchase_date = datetime.now(timezone.utc)

        db.session.commit()

        return booking, "تم تحديث الحجز بنجاح"
