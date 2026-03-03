from models.models import Helmets, db


class HelmetServices:

    # =========================
    # Get All Helmets
    # =========================
    @staticmethod
    def get_helmets():
        return Helmets.query.all()


    # =========================
    # Get Helmet By ID
    # =========================
    @staticmethod
    def get_helmet_by_id(helmet_id):
        return Helmets.query.get(helmet_id)


    # =========================
    # Create Helmet
    # =========================
    @staticmethod
    def create_helmet(data):

        helmet = Helmets(
            english_name=data.get("english_name"),
            arabic_name=data.get("arabic_name"),
            company=data.get("company"),
            price=data.get("price"),
            helmet_type=data.get("helmet_type"),
            colors=data.get("colors"),
            notes=data.get("notes"),
            status=data.get("status"),
            img_url=data.get("img_url")
        )

        db.session.add(helmet)
        db.session.commit()

        return helmet, "تم إضافة الخوذة بنجاح"


    # =========================
    # Update Helmet
    # =========================
    @staticmethod
    def update_helmet(helmet_id, data):

        helmet = Helmets.query.get(helmet_id)

        if not helmet:
            return None, "الخوذة غير موجودة"

        helmet.english_name = data.get("english_name")
        helmet.arabic_name = data.get("arabic_name")
        helmet.company = data.get("company")
        helmet.price = data.get("price")
        helmet.helmet_type = data.get("helmet_type")
        helmet.colors = data.get("colors")
        helmet.notes = data.get("notes")
        helmet.status = data.get("status")
        helmet.img_url = data.get("img_url")

        db.session.commit()

        return helmet, "تم التعديل بنجاح"