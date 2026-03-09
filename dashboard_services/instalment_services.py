from models.models import Instalments, db


class InstalmentServices:

    # =========================
    # Get Installment Rate (for agent)
    # =========================
    @staticmethod
    def get_installment_rate(months: int, down_payment_pct: float = 0) -> dict:
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

    # =========================
    # Get All
    # =========================
    @staticmethod
    def get_instalments():
        return Instalments.query.all()


    # =========================
    # Get By ID
    # =========================
    @staticmethod
    def get_instalment_by_id(instalment_id):
        return Instalments.query.get(instalment_id)


    # =========================
    # Create
    # =========================
    @staticmethod
    def create_instalment(form):

        instalment = Instalments(
            min_down_payment=form.get("min_down_payment"),
            max_down_payment=form.get("max_down_payment"),
            min_months=form.get("min_months"),
            max_months=form.get("max_months"),
            percentage=form.get("percentage")
        )

        db.session.add(instalment)
        db.session.commit()

        return instalment, "تم إضافة خطة التقسيط بنجاح"


    # =========================
    # Update
    # =========================
    @staticmethod
    def update_instalment(instalment_id, form):

        instalment = Instalments.query.get(instalment_id)

        if not instalment:
            return None, "الخطة غير موجودة"

        instalment.min_down_payment = form.get("min_down_payment")
        instalment.max_down_payment = form.get("max_down_payment")
        instalment.min_months = form.get("min_months")
        instalment.max_months = form.get("max_months")
        instalment.percentage = form.get("percentage")

        # recalculation (important)
        if instalment.percentage and instalment.max_months:
            instalment.percentage_per_month = round(
                float(instalment.percentage) / int(instalment.max_months), 4
            )
        else:
            instalment.percentage_per_month = 0

        db.session.commit()

        return instalment, "تم تعديل خطة التقسيط بنجاح"