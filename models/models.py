from flask_login import UserMixin
from datetime import datetime, timedelta , time 
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()



# =========================
# Users Table
# =========================
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
   
    


# =========================
# Clients Table
# =========================
class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)

    phone_number = db.Column(db.String(30), unique=True, nullable=False)

    chat_summary = db.Column(db.Text) # this col to keep the history 

    last_user_reply = db.Column(db.Text) # the current message
    last_bot_reply = db.Column(db.Text) # this col to enhance the context
    last_bot_reply_type = db.Column(db.String(50)) # this col to classify the message is followup or retarget or normal reply

    last_user_message_at = db.Column(db.DateTime) # this col to detect the users dosent reply
    last_bot_message_at = db.Column(db.DateTime) # this col to avoid spamming

    info = db.Column(db.Text) # this col for info about products the client bought (it will be fill by human ) 

    has_purchased = db.Column(db.Boolean, default=False) # this col to know the client bought or not (it will be fill by human ) 
    purchase_date = db.Column(db.DateTime) # this col we use in followup schadualing

    is_active = db.Column(db.Boolean, default=True) # this col help with users dont need to send any message

    created_at = db.Column(db.DateTime, default=datetime.utcnow) # this col will help us on analysis

    # Relationships
    followups = db.relationship("FollowUp", backref="client", lazy=True)
    complaints = db.relationship("Complaint", backref="client", lazy=True)


# =========================
# FollowUp Templates Table
# =========================
class FollowUpTemplate(db.Model):
    __tablename__ = "followup_templates"

    id = db.Column(db.Integer, primary_key=True)

    template_name = db.Column(db.String(100)) #followup message name 
    template_body = db.Column(db.Text) # followup message body

    followups = db.relationship("FollowUp", backref="template", lazy=True)


# =========================
# FollowUps Table (to schadual the follow ups with clients)
# =========================
class FollowUp(db.Model):
    __tablename__ = "followups"

    id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(db.Integer, db.ForeignKey("clients.id")) # to get his phone number and send the message

    template_id = db.Column(db.Integer, db.ForeignKey("followup_templates.id")) # select the template message

    scheduled_time = db.Column(db.DateTime) # this is the folowup time

    created_by_employee = db.Column(db.String(100)) # the name of emploee who creates the followup

    created_at = db.Column(db.DateTime, default=datetime.utcnow) 


# =========================
# Complaints Table
# =========================
class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(db.Integer, db.ForeignKey("clients.id")) 

    message_text = db.Column(db.Text) # the user message

    is_resolved = db.Column(db.Boolean, default=False) # human will check it

    resolved_at = db.Column(db.DateTime) 

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# Motors Table
# =========================
class Motors(db.Model):
    __tablename__ = "motors"

    id = db.Column(db.Integer, primary_key=True)

    english_name = db.Column(db.String(40))
    arabic_name = db.Column(db.String(40))
    
    company = db.Column(db.String(40))
    agency_name = db.Column(db.String(40))
    
    moto_type = db.Column(db.String(40)) #(motorcycle or scoter)
    price = db.Column(db.Integer)


    engin_capacity = db.Column(db.String(40))
    fule_capacity = db.Column(db.String(40))
    engin_type = db.Column(db.String(40))
    transmission_type = db.Column(db.String(40))
    max_speed = db.Column(db.String(40))
    brake_type = db.Column(db.String(40))
    colors = db.Column(db.String(100))
    notes = db.Column(db.String(100))
    
    
    is_available = db.Column(db.Boolean, default=True) 
    status = db.Column(db.String(40)) # (new or used)


    img_url = db.Column(db.String(200))



# =========================
# Helmet Table
# =========================
class Helmets(db.Model):
    __tablename__ = "helmets"

    id = db.Column(db.Integer, primary_key=True)

    english_name = db.Column(db.String(40))
    arabic_name = db.Column(db.String(40))
    
    company = db.Column(db.String(40))
    
    price = db.Column(db.Integer)


   
    helmet_type = db.Column(db.String(40))
    colors = db.Column(db.String(100))
    notes = db.Column(db.String(100))
    
    
    is_available = db.Column(db.Boolean, default=True) 
    status = db.Column(db.String(40)) # (new or used)


    img_url = db.Column(db.String(200))





# =========================
# Instalments Table
# =========================
class Instalments(db.Model):
    __tablename__ = "instalments"

    id = db.Column(db.Integer, primary_key=True)

    min_down_payment = db.Column(db.Integer) # min down payment
    max_down_payment = db.Column(db.Integer) # max down payment
    
    min_months = db.Column(db.Integer) # min number of months for this paln
    max_months = db.Column(db.Integer) # max number of months for this paln 
    
    percentage = db.Column(db.Float) # percentage for this plan
    percentage_per_month = db.Column(db.Float) # percentage for each month based (total_percentage/number_of_max_months)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.percentage and self.max_months:
            self.percentage_per_month = round(
                float(self.percentage) / int(self.max_months), 4
            )
        else:
            self.percentage_per_month = 0
    

