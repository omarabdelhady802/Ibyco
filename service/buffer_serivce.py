import redis

# الاتصال بـ Redis داخل Docker
r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

def add_to_buffer(platform_id, page_id, sender_id, text):
    """
    تجميع الرسائل المتتالية في مخزن Redis مؤقت
    """
    # المفتاح الأساسي اللي ليه TTL (المنبه)
    buffer_key = f"buffer:{platform_id}:{page_id}:{sender_id}"
    # المفتاح الظل اللي شايل النص (الخزنة)
    shadow_key = f"shadow:{buffer_key}"

    try:
        # 1. جلب النص المجمع القديم من الـ Shadow Key
        existing_text = r.get(shadow_key) or ""
        
        # 2. دمج النص الجديد (عمل Concat)
        new_concatenated_text = f"{existing_text} {text}".strip()
        
        # 3. تحديث الـ Shadow Key بنص طويل الأمد (ساعة مثلاً) لضمان بقائه
        r.setex(shadow_key, 3600, new_concatenated_text)
        
        # 4. تحديث مفتاح الـ TTL (المنبه) لـ 3 ثواني
        # أول ما المفتاح ده يختفي، الـ Redis Worker هيعرف إن الـ 3 ثواني خلصوا
        r.setex(buffer_key, 3, "trigger")
        
        print(f"[BUFFER] Message added for {sender_id}. Timer reset to 3s.")
        
    except Exception as e:
        print(f"[ERROR] Redis Buffer Error: {e}")
