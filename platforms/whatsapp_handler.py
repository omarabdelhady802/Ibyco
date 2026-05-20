import requests
from platforms.basehundelr import BaseChatHandler # تأكد من اسم الملف صح
from notified_center.Email_sender import EmailClient
email_client = EmailClient()

class WhatsAppHandler(BaseChatHandler):
    platform_id = 1

    def __init__(self, showroom_page):
        # بننادي الـ constructor بتاع الـ Base
        super().__init__(showroom_page)
        
        # سحب البيانات من الـ model
        self.phone_number_id = showroom_page.phone_id 
        self.version = "v19.0" 
        self.api_url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}"
        
        self.clean_key = str(self.api_key).strip() if self.api_key else ""
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.clean_key}"
        }

    # ميثود الـ send بتاعتك ممتازة مش محتاجة تعديل في الـ logic
    def send(self, sender_id, text):
        if not text or str(text).strip() == "":
            return None

        url = f"{self.api_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": sender_id,
            "text": {"body": str(text)}
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code not in [200, 201]:
                print(f"[ERROR] WhatsApp API Error: {response.text}")
                print("TOKEN:", self.clean_key[:20])
                print("PHONE_ID:", self.phone_number_id)
                print("URL:", self.api_url)
            return response
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            email_client.send_email(
                subject="[WHATSAPP HANDLER ERROR] Message Sending Failure in whatsapp_handler file",
                body=f"An error occurred while sending a message to {sender_id}:\n\n{str(e)}"
            )
            return None  