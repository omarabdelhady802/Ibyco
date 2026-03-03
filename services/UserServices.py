from models.models import Users, db


# =========================
# Create User
# =========================
def create_user(name, password):

    # Validate username uniqueness
    existing_user = Users.query.filter_by(name=name).first()

    if existing_user:
        return None, "هذا الاسم موجود بالفعل"

    user = Users(
        name=name,
        password=password
    )

    db.session.add(user)
    db.session.commit()

    return user, "تم تسجيل المستخدم بنجاح"


# =========================
# Update User With Validation
# =========================
def update_user(user_id, name=None, password=None):

    user = Users.query.get(user_id)

    if not user:
        return None, "هذا المستخدم غير موجود"

    # Validate name uniqueness (if name is changing)
    if name and name != user.name:

        existing_user = Users.query.filter_by(name=name).first()

        if existing_user:
            return None, "هذا الاسم موجود بالفعل"

        user.name = name

    # Update password if provided
    if password:
        user.password = password

    db.session.commit()

    return user, "تم التعديل بنجاح"


# =========================
# Login Verification
# =========================
def verify_login(name, password):

    user = Users.query.filter_by(name=name, password=password).first()

    if not user:
        return None

    return user


# =========================
# Get User By ID
# =========================
def get_user_by_id(user_id):
    user = Users.query.get(user_id)
    if user :
        return user
    else:
        return None

# =========================
# Get All Users 
# =========================
def get_users():
    users = Users.query.all()   
    return users
    


