from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, time, date, timezone
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models.models import *
from dashboard_services import UserServices
from dashboard_services.followup_template_services import FollowUpTemplateServices
from dashboard_services.helmet_services import HelmetServices
from dashboard_services.instalment_services import InstalmentServices
from dashboard_services.motor_services import MotorServices
from dashboard_services.booking_services import BookingServices
import threading
from parsers.whatsapp import parse_whatsapp_message  
from service.redis_worker import add_to_buffer, start_redis_listener 
from service.message_processor import process_message
from dashboard_services.showroom_page_services import ShowroomPageServices








# configrations app
app = Flask(__name__)
import os
_db_path = os.path.join(os.path.dirname(__file__), "instance", "Ibyco.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{_db_path}'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False 
login_manager = LoginManager(app)
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()
#######################################################



@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))



#routes

#login page
@app.route('/',methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("users"))
    if request.method == 'POST':
        username =request.form.get('username')
        password =request.form.get('password')
        user  = UserServices.verify_login(username , password)
        

        if user:
            login_user(user)
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('users'))
        else:
            flash('اسم المستخدم او كلمه المرور غير صحيحه', 'danger')
    return render_template('index.html')

    


# start of users routes

# this route for display users
@app.route('/users')
@login_required
def users():
    users_list = UserServices.get_users()

    return render_template('users.html', users=users_list)


# this route for add new user in db
@app.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        user , msg = UserServices.create_user(name, password)
        if user :
            flash(msg,'success')
        else :
            flash(msg,"danger")
 
        return redirect(url_for('users'))

    return render_template('new_user.html')


#this route for edit user
@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = UserServices.get_user_by_id(user_id)
    if not user :
        flash("هذا المستخدم غير موجود ","danger")
        return redirect(url_for('users'))

    if request.method == 'POST':
        password = request.form.get('password')
        name = request.form.get('name')
        user, msg = UserServices.update_user(user_id , name,password)
        if user :
            flash(msg,'success')
        else :
            flash(msg,"danger")
        return redirect(url_for('users'))

    return render_template('edit_user.html', user=user)
# end of users routes


# start for helmets routes 

# this route for display helmets 
@app.route('/helmets')
@login_required
def helmets():
    helmets_list = HelmetServices.get_helmets()
    return render_template("helmets.html", helmets=helmets_list)


# this route for create new helmet 
@app.route('/helmets/new', methods=['GET','POST'])
@login_required
def new_helmet():

    if request.method == "POST":

        helmet, msg = HelmetServices.create_helmet(request.form)

        if helmet:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("helmets"))

    return render_template("new_helmet.html")


# this route for edit helmet 
@app.route('/helmets/edit/<int:helmet_id>', methods=['GET','POST'])
@login_required
def edit_helmet(helmet_id):

    helmet = HelmetServices.get_helmet_by_id(helmet_id)

    if not helmet:
        flash("الخوذة غير موجودة", "danger")
        return redirect(url_for("helmets"))

    if request.method == "POST":

        helmet, msg = HelmetServices.update_helmet(
            helmet_id,
            request.form
        )

        if helmet:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("helmets"))

    return render_template("edit_helmet.html", helmet=helmet)

# end of helmets routes



# start routes for motorcycle

# this route for display motors
@app.route('/motors')
@login_required
def motors():

    motors_list = MotorServices.get_motors()

    return render_template(
        "motors.html",
        motors=motors_list
    )


# this route for add new motor
@app.route('/motors/new', methods=['GET','POST'])
@login_required
def new_motor():

    if request.method == "POST":

        motor, msg = MotorServices.create_motor(request.form)

        if motor:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("motors"))

    return render_template("new_motor.html")


# this route for edit motor 
@app.route('/motors/edit/<int:motor_id>', methods=['GET','POST'])
@login_required
def edit_motor(motor_id):

    motor = MotorServices.get_motor_by_id(motor_id)

    if not motor:
        flash("الموتوسيكل غير موجود", "danger")
        return redirect(url_for("motors"))

    if request.method == "POST":

        motor, msg = MotorServices.update_motor(
            motor_id,
            request.form
        )

        if motor:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("motors"))

    return render_template(
        "edit_motor.html",
        motor=motor
    )

# end of motor routes


# start followup template routes

# display templates
@app.route('/followup_templates')
@login_required
def followup_templates():

    templates = FollowUpTemplateServices.get_templates()

    return render_template(
        "followup_templates.html",
        templates=templates
    )

# add new template
@app.route('/followup_templates/new', methods=['GET','POST'])
@login_required
def new_followup_template():

    if request.method == "POST":

        template, msg = FollowUpTemplateServices.create_template(
            request.form
        )

        if template:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("followup_templates"))

    return render_template("new_followup_template.html")

# this route for update templates
@app.route('/followup_templates/edit/<int:template_id>', methods=['GET','POST'])
@login_required
def edit_followup_template(template_id):

    template = FollowUpTemplateServices.get_template_by_id(template_id)

    if not template:
        flash("القالب غير موجود", "danger")
        return redirect(url_for("followup_templates"))

    if request.method == "POST":

        template, msg = FollowUpTemplateServices.update_template(
            template_id,
            request.form
        )

        if template:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("followup_templates"))

    return render_template(
        "edit_followup_template.html",
        template=template
    )

# end of followup template routes




# start routes for installments

# this route for display installment plans
@app.route('/instalments')
@login_required
def instalments():

    instalments = InstalmentServices.get_instalments()

    return render_template(
        "instalments.html",
        instalments=instalments
    )


# this route for add new instalment plan 
@app.route('/instalments/new', methods=['GET','POST'])
@login_required
def new_instalment():

    if request.method == "POST":

        instalment, msg = InstalmentServices.create_instalment(
            request.form
        )

        if instalment:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("instalments"))

    return render_template("new_instalment.html")


# this route for edit plan
@app.route('/instalments/edit/<int:instalment_id>', methods=['GET','POST'])
@login_required
def edit_instalment(instalment_id):

    instalment = InstalmentServices.get_instalment_by_id(instalment_id)

    if not instalment:
        flash("الخطة غير موجودة", "danger")
        return redirect(url_for("instalments"))

    if request.method == "POST":

        instalment, msg = InstalmentServices.update_instalment(
            instalment_id,
            request.form
        )

        if instalment:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("instalments"))

    return render_template(
        "edit_instalment.html",
        instalment=instalment
    )


# end routes for instalments


# start routes for complaints

# this route for display complaints which are not solved
@app.route("/complaints")
@login_required
def complaints():

    complaints = Complaint.query.filter_by(is_resolved=False).all()

    return render_template("complaints.html", complaints=complaints)



# this route for display complaint in details
@app.route("/complaints/view/<int:id>", methods=["GET", "POST"])
@login_required
def view_complaint(id):

    complaint = Complaint.query.get_or_404(id)

    if request.method == "POST":

        is_resolved = request.form.get("is_resolved")

        if is_resolved == "1":
            complaint.is_resolved = True
            complaint.resolved_at = datetime.now(timezone.utc)
        else:
            complaint.is_resolved = False
            complaint.resolved_at = None

        db.session.commit()

        return redirect(url_for("complaints"))

    return render_template("view_complaint.html", complaint=complaint)

# end routes for complaints


# start routes for booking

# this route for display all booking
@app.route("/bookings", methods=["GET", "POST"])
@login_required
def bookings():

    phone = None

    if request.method == "POST":
        phone = request.form.get("phone")

    bookings = BookingServices.get_bookings_by_phone(phone)

    return render_template(
        "bookings.html",
        bookings=bookings,
        phone=phone
    )


# this route for view and update book and client info 
@app.route("/booking/<int:booking_id>", methods=["GET", "POST"])
@login_required
def booking_details(booking_id):

    booking = BookingServices.get_booking_by_id(booking_id)

    if not booking:
        flash("الحجز غير موجود", "danger")
        return redirect(url_for("booking.bookings"))

    if request.method == "POST":

        booking, msg = BookingServices.update_booking_and_client(
            booking_id,
            request.form
        )

        if booking:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("bookings"))

    return render_template(
        "booking_details.html",
        booking=booking,
        client=booking.client
    )


# routes for pages info 

# this route for display pages
@app.route('/pages')
@login_required
def pages():

    pages = ShowroomPageServices.get_pages()

    return render_template(
        "pages.html",
        pages=pages
    )


# this route for add new page
@app.route('/pages/new', methods=['GET','POST'])
@login_required
def new_page():

    if request.method == "POST":

        page, msg = ShowroomPageServices.create_page(
            request.form
        )

        if page:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("pages"))

    return render_template("new_page.html")


# this route for edit page
@app.route('/pages/edit/<int:page_id>', methods=['GET','POST'])
@login_required
def edit_page(page_id):

    page = ShowroomPageServices.get_page_by_id(page_id)

    if not page:
        flash("الصفحة غير موجودة", "danger")
        return redirect(url_for("pages"))

    if request.method == "POST":

        page, msg = ShowroomPageServices.update_page(
            page_id,
            request.form
        )

        if page:
            flash(msg, "success")
        else:
            flash(msg, "danger")

        return redirect(url_for("pages"))

    return render_template(
        "edit_page.html",
        page=page
    )



# this route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))




# ── Agent Chat API ──────────────────────────────────────────────────

from graph.agent_graph import get_agent
from graph.agent_response import AgentResponse
from dashboard_services.client_services import ClientServices


@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    client_data = data.get("client")
    client_id = client_data.get("id") if client_data else None
    client = ClientServices.get_client_by_id(client_id) if client_id else None

    state = {
        "client":               client,
        "current_message":      data.get("message", ""),
        "intent":               None,
        "filters":              {},
        "vehicles":             [],
        "lead":                 data.get("lead") or {},
        "booking_stage":        None,
        "response":             None,
        "recommendations":      [],
        "complaint_saved":      None,
        "booking_saved":        None,
        "ask_clarification":    None,
        "intent_usage":         None,
        "usage":                None,
    }

    result = get_agent().invoke(state)

    return jsonify(AgentResponse.from_result(result).to_dict())






VERIFY_TOKEN = "dangerMO"

@app.route("/webhook", methods=["GET", "POST"])
def whatsapp_webhook():
    # 1. جزء التفعيل (Verification)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("[INFO] Webhook Verified!")
            return challenge, 200
        return "Verification failed", 403

    # 2. جزء استقبال الرسائل (POST)
    if request.method == "POST":
        payload = request.json
        incoming_msg = parse_whatsapp_message(payload)
        
        if incoming_msg:
            try:
                # استخراج الـ Phone ID من مسار Meta
                value = payload['entry'][0]['changes'][0]['value']
                page_id = value['metadata']['phone_number_id']
                
                # الفصل بين النص والميديا
                if incoming_msg.type == "text":
                    # إرسال للنص للمخزن المؤقت (Redis)
                    add_to_buffer(
                        platform_id=1,           
                        page_id=page_id,         
                        sender_id=incoming_msg.sender_id, 
                        text=incoming_msg.text
                    )
                    print(f"[WEBHOOK] Text from {incoming_msg.sender_id} sent to buffer.")
                
                else:
                    # ميديا (صورة، فيديو، إلخ) -> معالجة فورية بدون انتظار الـ Buffer
                    print(f"[WEBHOOK] Media ({incoming_msg.type}) detected. Processing immediately...")
                    
                    # بنحتاج نمرر الـ phone_number_id عشان الـ processor يعرف الصفحة
                    incoming_msg.phone_number_id = page_id
                    
                    # استدعاء المعالجة مباشرة داخل الـ context بتاع الـ app
                    with app.app_context():
                        process_message(incoming_msg)

            except Exception as e:
                print(f"[ERROR] Webhook processing failed: {e}")

    # الرد بـ 200 دايماً لشركة Meta
    return "OK", 200

if __name__ == "__main__":
   
 
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=False,use_reloader=False)

