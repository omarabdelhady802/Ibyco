from flask import Flask, render_template, request, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta , time ,date
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models.models import *
from dashboard_services import UserServices
from dashboard_services.followup_template_services import FollowUpTemplateServices
from dashboard_services.helmet_services import HelmetServices
from dashboard_services.instalment_services import InstalmentServices
from dashboard_services.motor_services import MotorServices




# configrations app
app = Flask(__name__)
import os
_db_path = os.path.join(os.path.dirname(__file__), "instance", "Ibyco.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{_db_path}'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False  # Disable auto-commit
login_manager = LoginManager(app)
db.init_app(app)
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



# this route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host= "0.0.0.0" , port = 5000 ,debug=True)


