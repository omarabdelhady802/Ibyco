import logging
import traceback
from service.message_processor import IncomingMessage

logger = logging.getLogger(__name__)

def parse_whatsapp_message(payload):
    """
    تحليل رسائل WhatsApp Cloud API الرسمية
    """
    try:
        # 1. التحقق الأساسي وتجاوز التنبيهات غير المتعلقة بالرسائل (مثل الـ Status)
        if not isinstance(payload, dict):
            return None

        # هيكل واتساب الرسمي: entry -> changes -> value -> messages
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        if "messages" not in value:
            # قد تكون تحديثات حالة (sent, delivered, read) نتجاهلها هنا
            return None

        message_data = value["messages"][0]
        sender_id = message_data.get("from") # رقم هاتف المرسل
        msg_type = message_data.get("type")  # نوع الرسالة (text, image, document, etc.)

        if not sender_id:
            logger.warning("WhatsApp payload received without 'from' field")
            return None

        # 2. معالجة الرسائل النصية
        if msg_type == "text":
            return IncomingMessage(
                sender_id=sender_id,
                msg_type="text",
                text=message_data.get("text", {}).get("body")
            )

        # 3. معالجة الميديا (صور، فيديو، صوت، مستندات)
        # في API الرسمي، الميديا تأتي ككائن يحمل الـ id والـ caption (إن وجد)
        media_types = ["image", "video", "audio", "document", "voice", "sticker"]
        
        if msg_type in media_types:
            media_obj = message_data.get(msg_type)
            # نقوم بتمرير الـ media_id بدلاً من الكائن كاملاً لسهولة التعامل لاحقاً
            # أو تمرير الكائن كما هو ليستخدمه الـ Handler
            media_info = {
                "id": media_obj.get("id"),
                "mime_type": media_obj.get("mime_type"),
                "caption": media_obj.get("caption", ""), # التعليق المصاحب للصورة
                "filename": media_obj.get("filename", "") # للمستندات
            }

            return IncomingMessage(
                sender_id=sender_id,
                msg_type=msg_type,
                text=media_info["caption"] if msg_type in ["image", "video"] else "",
                media=media_info # هذا هو الـ id الذي سيستخدمه الـ download_image
            )

        return None

    except Exception as e:
        full_error = f"Fatal Error in parse_whatsapp_message:\n{traceback.format_exc()}\nPayload Data: {payload}"
        logger.critical(full_error)
        
        # إرسال إيميل في حالة الخطأ الجسيم فقط
        
        return None