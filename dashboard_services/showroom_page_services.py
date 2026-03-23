from models.models import ShowroomPage, db


class ShowroomPageServices:

    # =========================
    # Get All Pages
    # =========================
    @staticmethod
    def get_pages():
        return ShowroomPage.query.all()


    # =========================
    # Get Page By ID
    # =========================
    @staticmethod
    def get_page_by_id(page_id):
        return ShowroomPage.query.get(page_id)


    # =========================
    # Create Page
    # =========================
    @staticmethod
    def create_page(form):

        page_id = form.get("page_id")
        page_token = form.get("page_token")
        phone_id = form.get("phone_id")
        platform_id = form.get("platform_id")

        existing = ShowroomPage.query.filter_by(page_id=page_id).first()

        if existing:
            return None, "هذا الـ Page ID مسجل بالفعل"

        page = ShowroomPage(
            page_id=page_id,
            page_token=page_token,
            phone_id=phone_id,
            platform_id=platform_id,
            is_active=True
        )

        db.session.add(page)
        db.session.commit()

        return page, "تم اضافة الصفحة بنجاح"


    # =========================
    # Update Page
    # =========================
    @staticmethod
    def update_page(page_id_db, form):

        page = ShowroomPage.query.get(page_id_db)

        if not page:
            return None, "الصفحة غير موجودة"

        new_page_id = form.get("page_id")

        # Validate unique page_id
        if new_page_id != page.page_id:
            existing = ShowroomPage.query.filter_by(page_id=new_page_id).first()
            if existing:
                return None, "هذا الـ Page ID مستخدم بالفعل"

        page.page_id = new_page_id
        page.page_token = form.get("page_token")
        page.phone_id = form.get("phone_id")
        page.platform_id = form.get("platform_id")
        page.is_active = True if form.get("is_active") else False

        db.session.commit()

        return page, "تم تعديل الصفحة بنجاح"