from models.models import Motors, db


class MotorServices:

    # =========================
    # Get All Motors
    # =========================
    @staticmethod
    def get_motors():
        return Motors.query.all()


    # =========================
    # Get Motor By ID
    # =========================
    @staticmethod
    def get_motor_by_id(motor_id):
        return Motors.query.get(motor_id)


    # =========================
    # Create Motor
    # =========================
    @staticmethod
    def create_motor(data):

        motor = Motors(
            english_name=data.get("english_name"),
            arabic_name=data.get("arabic_name"),
            company=data.get("company"),
            agency_name=data.get("agency_name"),
            moto_type=data.get("moto_type"),
            price=data.get("price"),
            engin_capacity=data.get("engin_capacity"),
            fule_capacity=data.get("fule_capacity"),
            engin_type=data.get("engin_type"),
            transmission_type=data.get("transmission_type"),
            max_speed=data.get("max_speed"),
            brake_type=data.get("brake_type"),
            colors=data.get("colors"),
            notes=data.get("notes"),
            status=data.get("status"),
            img_url=data.get("img_url")
        )

        db.session.add(motor)
        db.session.commit()

        return motor, "تم إضافة الموتوسيكل بنجاح"


    # =========================
    # Update Motor
    # =========================
    @staticmethod
    def update_motor(motor_id, data):

        motor = Motors.query.get(motor_id)

        if not motor:
            return None, "الموتوسيكل غير موجود"

        motor.english_name = data.get("english_name")
        motor.arabic_name = data.get("arabic_name")
        motor.company = data.get("company")
        motor.agency_name = data.get("agency_name")
        motor.moto_type = data.get("moto_type")
        motor.price = data.get("price")
        motor.engin_capacity = data.get("engin_capacity")
        motor.fule_capacity = data.get("fule_capacity")
        motor.engin_type = data.get("engin_type")
        motor.transmission_type = data.get("transmission_type")
        motor.max_speed = data.get("max_speed")
        motor.brake_type = data.get("brake_type")
        motor.colors = data.get("colors")
        motor.notes = data.get("notes")
        motor.status = data.get("status")
        motor.img_url = data.get("img_url")

        db.session.commit()

        return motor, "تم التعديل بنجاح"