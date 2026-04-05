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

        query = Booking.query.join(Client)

        if phone:
            query = query.filter(Client.phone_number.ilike(f"%{phone}%"))
        else:
            query = query.filter(
                Booking.status.notin_(["completed", "canceled"])
            )

        return query.all()
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
    def create_booking(client, purpose=None, date=None):
        booking = Booking(
            client_id=client.id if client else None,
            purpose=purpose,
            date=date,
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
            
            from datetime import datetime, timezone
            client.has_purchased = "has_purchased" in form  # True if checked, False if unchecked
            if client.has_purchased and not client.purchase_date:
                client.purchase_date = datetime.now(timezone.utc)

        db.session.commit()

        return booking, "تم تحديث الحجز بنجاح"
