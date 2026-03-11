from datetime import datetime, timezone
from models.models import Complaint, db


class ComplaintServices:

    # =========================
    # Get All Complaints
    # =========================
    @staticmethod
    def get_complaints():
        return (
            Complaint.query
            .order_by(Complaint.created_at.desc())
            .all()
        )

    # =========================
    # Get Complaint By ID
    # =========================
    @staticmethod
    def get_complaint_by_id(complaint_id):
        return Complaint.query.get(complaint_id)

    # =========================
    # Create Complaint (for agent use)
    # =========================
    @staticmethod
    def create_complaint(client, message_text):
        complaint = Complaint(
            client_id=client.id if client else None,
            message_text=message_text,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(complaint)
        db.session.commit()

        return complaint.id

    # =========================
    # Resolve Complaint
    # =========================
    @staticmethod
    def resolve_complaint(complaint_id):

        complaint = Complaint.query.get(complaint_id)

        if not complaint:
            return None, "الشكوى غير موجودة"

        complaint.is_resolved = True
        complaint.resolved_at = datetime.now(timezone.utc)

        db.session.commit()

        return complaint, "تم حل الشكوى بنجاح"
