from models.models import ShowroomPage, Client, db
from graph.agent_graph import get_agent
from graph.agent_response import AgentResponse
from sqlalchemy.exc import IntegrityError
from notified_center.Email_sender import EmailClient
email_client = EmailClient()


class IncomingMessage:
    def __init__(self, sender_id, msg_type, text=None, media=None, phone_number_id=None):
        self.sender_id       = sender_id
        self.type            = msg_type
        self.text            = text
        self.media           = media
        self.phone_number_id = phone_number_id


def run_agent(client, message_text):
    state = {
        "client":            client,
        "current_message":   message_text,
        "intent":            None,
        "filters":           {},
        "vehicles":          [],
        "lead":              {},
        "booking_stage":     None,
        "response":          None,
        "recommendations":   [],
        "complaint_saved":   None,
        "booking_saved":     None,
        "ask_clarification": None,
        "intent_usage":      None,
        "usage":             None,
    }

    result = get_agent().invoke(state)
    response_obj = AgentResponse.from_result(result)
    reply_text = response_obj.response

    # الـ response_node بيعمل commit للـ DB عبر ClientServices.update_client_turn
    # مش محتاجين نعمل commit تاني هنا

    return reply_text


def process_message(message):
    # 1. جلب أو إنشاء العميل

# 1. بنحاول ندور على العميل
    client = Client.query.filter_by(phone_number=message.sender_id).first()

    if not client:
      try:
        # 2. لو مش موجود بنحاول نضيفه
        client = Client(phone_number=message.sender_id)
        db.session.add(client)
        db.session.commit()
      except IntegrityError:
           # 3. لو حصل Error معناها إن Thread تاني ضافه في نفس الأجزاء من الثانية
        db.session.rollback() # بنلغي العملية عشان السشن متبوظش
        client = Client.query.filter_by(phone_number=message.sender_id).first() # بنجيبه تاني

    # 2. جلب بيانات الـ page (التوكن وغيره)
    page = ShowroomPage.query.filter_by(phone_id=message.phone_number_id).first()

    try:
        from platforms.whatsapp_handler import WhatsAppHandler
        handler = WhatsAppHandler(page)
        reply = handler.handle(message, client)
        if reply:
            handler.send(message.sender_id, reply)
    except Exception as e:
        print(f"[PROCESSOR ERROR] {e}")
        email_client.send_email(
            subject="[PROCESSOR ERROR] Message Processing Failure in process_message file",
            body=f"An error occurred while processing a message from {message.sender_id}:\n\n{str(e)}"
        )