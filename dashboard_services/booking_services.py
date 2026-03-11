from models.models import Client,db,Booking
from datetime import datetime


def get_bookings_by_phone(phone=None):

    query = Booking.query.join(Client)

    if phone:
        query = query.filter(Client.phone_number.ilike(f"%{phone}%"))
    else:
        query = query.filter(
            Booking.status.notin_(["completed", "canceled"])
        )

    return query.all()

def get_booking_by_id(booking_id):
    return Booking.query.get(booking_id)


def update_booking_and_client(booking_id, form):

    booking = Booking.query.get(booking_id)

    if not booking:
        return None, "الحجز غير موجود"

    client = booking.client

    # -------- booking update --------
    booking.status = form.get("status")

    # -------- client update --------
    client.info = form.get("info")

    has_purchase = form.get("has_purchase")

    if has_purchase:
        client.has_purchased = True

        # auto purchase date
        if not client.purchase_date:
            client.purchase_date = datetime.utcnow()

    db.session.commit()

    return booking, "تم تحديث البيانات بنجاح"