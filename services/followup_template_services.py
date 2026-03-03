from models.models import FollowUpTemplate, db


class FollowUpTemplateServices:

    # =========================
    # Get All Templates
    # =========================
    @staticmethod
    def get_templates():
        return FollowUpTemplate.query.all()


    # =========================
    # Get Template By ID
    # =========================
    @staticmethod
    def get_template_by_id(template_id):
        return FollowUpTemplate.query.get(template_id)


    # =========================
    # Create Template
    # =========================
    @staticmethod
    def create_template(form):

        template = FollowUpTemplate(
            template_name=form.get("template_name"),
            template_body=form.get("template_body")
        )

        db.session.add(template)
        db.session.commit()

        return template, "تم إضافة قالب المتابعة بنجاح"


    # =========================
    # Update Template
    # =========================
    @staticmethod
    def update_template(template_id, form):

        template = FollowUpTemplate.query.get(template_id)

        if not template:
            return None, "القالب غير موجود"

        template.template_name = form.get("template_name")
        template.template_body = form.get("template_body")

        db.session.commit()

        return template, "تم التعديل بنجاح"