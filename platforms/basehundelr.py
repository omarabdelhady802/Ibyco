import json
import re
import traceback
from service.message_processor import run_agent


class BaseChatHandler:
    platform_id = None

    def __init__(self, showroom_page):
        self.showroom_page = showroom_page
        self.page_id  = showroom_page.page_id
        self.api_key  = showroom_page.page_token
      
    def handle(self, message, client): # اضفنا العميل هنا
        if message.type == "text":
            return self.handle_text(text=message.text, client=client, sender_id=message.sender_id)
        
        return self.handle_media(message.type, message.media)

    def handle_text(self, text, client, sender_id=None):
        """
        معالجة النصوص مباشرة عبر الـ Graph الموحد
        """
        # الـ run_agent هي اللي بتعمل الـ invoke والـ commit للـ DB
        reply_text = run_agent(client, text)
        
        return reply_text

    def handle_media(self, msg_type, media):
        responses = {
            "video": "برجاء ارسال رسالة نصية بدلاً من الفيديو.",
            "audio": "برجاء ارسال رسالة نصية بدلاً من الملف الصوتي.",
            "voice": "برجاء ارسال رسالة نصية بدلاً من الرسالة الصوتية.", 
            "location": "📍 تم استلام الموقع بنجاح."
        }
        return responses.get(msg_type, "📎 تم استلام المرفق.")

    def send(self, sender_id, text): 
        raise NotImplementedError("لازم تعمل override للميثود دي في الـ WhatsAppHandler")