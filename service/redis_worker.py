import os
import redis
from service.message_processor import process_message, IncomingMessage

r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

def add_to_buffer(platform_id: int, page_id: str, sender_id: str, text: str, ttl: int = 5):
    buffer_key = f"buffer:{platform_id}:{page_id}:{sender_id}"
    shadow_key = f"shadow:{buffer_key}"

    existing = r.get(shadow_key)
    if existing:
        combined = existing + "\n" + text
    else:
        combined = text

    r.set(shadow_key, combined)
    r.set(buffer_key, "1", ex=ttl)

    print(f"[BUFFER] Added message for {sender_id} | TTL={ttl}s")


def start_redis_listener():
    pubsub = r.pubsub()
    pubsub.psubscribe("__keyevent@0__:expired")
    print("[REDIS WORKER] Listening for expired buffers...")

    for message in pubsub.listen():
        if message['type'] == 'pmessage':
            key = message['data']
            if key.startswith("buffer:"):
                handle_expired_buffer(key)


def handle_expired_buffer(key):
    try:
        parts = key.split(":",3)
        if len(parts) < 4:
            return

        platform_id = parts[1]
        page_id     = parts[2]
        sender_id   = parts[3]

        shadow_key = f"shadow:{key}"

        # الحل هنا: نستخدم r.getset() أو r.get() متبوعة بـ r.delete() فوراً
        # الأفضل نجيب البيانات ونمسح المفتاح فوراً قبل ما الـ AI يبدأ
        final_text = r.get(shadow_key)

        if not final_text:
            return  # لو المفتاح مش موجود (Thread تاني مسحه)، اخرج فوراً

        # 1. امسح المفتاح فوراً "قبل" المعالجة
        r.delete(shadow_key) 
        
        print(f"[WORKER] Processing messages for {sender_id}...")

        incoming_msg = IncomingMessage(
            sender_id=sender_id,
            msg_type="text",
            text=final_text,
            phone_number_id=page_id
        )

        from app import app
        with app.app_context():
            # 2. دلوقتي لو الـ AI خد وقت، أي نسخة تانية مش هتلاقي الـ shadow_key
            process_message(incoming_msg)

    except Exception as e:
        print(f"[WORKER ERROR] {e}")






# 🔴 THIS WAS MISSING
if __name__ == "__main__":
    print("[WORKER] Starting Redis worker...")
    start_redis_listener()
