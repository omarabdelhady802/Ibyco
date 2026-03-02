from flask import Flask, render_template, request, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta , time ,date
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models.models import *




# configrations app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Ibyco.db'
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
        user = Users.query.filter_by(name=username, password=password).first()
        

        if user:
            login_user(user)
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('users'))
        else:
            flash('اسم المستخدم او كلمه المرور غير صحيحه', 'danger')
    return render_template('index.html')

    




