"""
Intent Node: Gemini Flash (via OpenRouter) classifies the user message into intent, product_type, and filters.
"""
import json
import re
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState
from llm.gemini import get_gemini
from dashboard_services.vehicle_query_services import get_all_brands, get_vehicle_by_name

SYSTEM_PROMPT = """You are an intelligent assistant for "ibyco" motorcycle and accessories showroom.
Your task is to analyse the customer's CURRENT message combined with the conversation history (Client history summary + Last bot reply) and extract intent and structured information.
The customer may write in Arabic (Egyptian dialect), English, or mixed — you must understand all.

IMPORTANT: Fill every JSON field using ALL available context — the current message AND the conversation history.
Only carry forward context from previous messages if the current message is a CONTINUATION of the same topic (e.g. answering a question the bot asked, or adding more detail to the same request).
If the customer is clearly asking about something NEW or DIFFERENT, start fresh — do NOT carry forward old vehicle names, filters, or down payments from previous turns.

Signs of a topic CONTINUATION (carry forward previous context):
- Customer is answering a question the bot asked (e.g. bot asked for down payment, customer replies with a number)
- Customer adds detail to the same vehicle (e.g. "عايز اعرف التقسيط" after asking about a specific model)
- Customer says "طيب" or "تمام" followed by more detail about the SAME vehicle

Signs of a topic SWITCH (start fresh, ignore old filters):
- Customer mentions a DIFFERENT product name than before
- Customer asks a completely new question unrelated to the previous topic
- Customer uses phrases like "غير كده", "ايه عندكم تاني", "عندكم غير ده", "خليني اشوف حاجة تانية"
- Customer asks about a different product type (e.g. was asking about motorcycle, now asks about scooter)

Return JSON only (no extra text) in this format:
{
  "intent": "browse | filter | details | installment | compare | booking | complaint | greeting | other",
  "product_type": "motorcycle | scooter | helmet | null",
  "filters": {
    "max_price": <number or null>,
    "min_price": <number or null>,
    "company": "<brand name or null>",
    "vehicle_name": "<first model name or null>",
    "vehicle_name_2": "<second model name for comparison or null>",
    "months": <number of installment months or null — e.g. 9 or 36>,
    "max_installment_12": <max acceptable monthly payment as number or null>,
    "transmission": "يدوي | أوتوماتيك | null",
    "down_payment": <down payment amount in EGP as number or null — e.g. 5000>,
    "show_more": <true if the customer is asking to see MORE products beyond what was already shown — e.g. "فيه تاني؟", "ورينى تاني", "show me more", "عندكم غير كده", "ايه كمان" — otherwise false>
  },
  "lead_info": {
    "name": "<customer name or null>",
    "phone": "<phone number or null>",
    "booking_purpose": "<reason for booking: test ride, purchase, inquiry, service — or null>",
    "appointment_date": "<requested date or time mentioned by customer e.g. 'tomorrow', 'Saturday', '15 March' — or null>"
  }
}

Intent definitions:
- browse: wants to see products generally, asks "what do you have", "what's available", "latest model", "price ranges" without specifying a number
- filter: wants to filter by a specific price number, brand, installment, or criteria (e.g. "suitable for kids", "cheapest", "budget of X EGP")
- details: asks about a specific model BY NAME (e.g. "tell me about jet x", "specs of haojue k4")
- installment: asks about installment plans, payment methods, or monthly payments FOR A SPECIFIC VEHICLE (not general questions about papers/documents)
- compare: wants to compare two models (extract vehicle_name and vehicle_name_2)
- booking: wants to book an appointment, visit, or buy (e.g. "I want to buy", "book a test ride", "accept invitation to the showroom"). IMPORTANT: booking ONLY when the customer EXPLICITLY says yes to booking (e.g. "اه", "تمام", "اوك", "ماشي", "yes", "احجزلي"). If the customer replies with a product name or anything else after a booking suggestion, it is NOT booking — classify based on what they actually said.
- complaint: complaining about a product, service, or bad experience
- greeting: general greeting or small talk
- other: general questions not directly about a specific product (e.g. offers, working hours, branches, oils, accessories, after-sales service)

Important rules:
- If the customer mentions a product NOT in the catalog (oils, accessories, spare parts) → intent = "other" even if a model name is mentioned
- If asking about offers/discounts without mentioning a product → intent = "other"
- If asking about working hours, branches, or address → intent = "other"
- If asking about installment papers/documents (الأوراق المطلوبة للتقسيط) without a specific vehicle → intent = "other"
- "latest model" or "newest release" without a specific name = browse, NOT details
- details ONLY when the model name is explicitly mentioned
- For booking intent: always try to infer booking_purpose from context. 
  If the customer was previously asking about a specific vehicle → booking_purpose = "test ride" or "purchase".
  If the customer was asking general questions → booking_purpose = "inquiry".
  Never leave booking_purpose null if there is any context available — make a reasonable inference.
Product type definitions:
- motorcycle: موتوسيكل / motorbike / دراجة نارية
- scooter: اسكوتر / سكوتر / scooter
- helmet: خوذة / هيلمت / helmet
- null: unspecified (default: motorcycle)"""


def intent_node(state: AgentState) -> dict:
    llm = get_gemini()
    message = state["current_message"]
    try:
        known_brands_set = get_all_brands()  # set for lookup
        known_brands_str = ", ".join(sorted(known_brands_set))
    except Exception:
        known_brands_set = {"sym", "honda", "yamaha", "haojue", "keeway","هاوجى","vigory","dayun"}
        known_brands_str = "sym, honda, yamaha, haojue, keeway ,هاوجى ,vigory ,dayun ,بينيللى"

    system = SYSTEM_PROMPT.replace(
        "- null: unspecified (default: motorcycle)",
        f"- null: unspecified (default: motorcycle)\n\nKnown brands/companies in catalog (use company field for these): {known_brands_str}\nAnything else that is not a known brand → treat as vehicle_name, NOT company."
    )

   
    client = state.get("client")
    chat_summary  = (client.chat_summary   or "") if client else ""
    last_bot_reply = (client.last_bot_reply or "") if client else ""

    client_ctx = ""
    if chat_summary:
        client_ctx += f"\nClient history summary:\n{chat_summary}"
    if last_bot_reply:
        client_ctx += f"\nLast bot reply to this client:\n{last_bot_reply}"

    system = system + client_ctx if client_ctx else system

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=message),
    ]

    intent_usage = {}
    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}
        meta = getattr(response, "usage_metadata", None) or getattr(response, "response_metadata", {}).get("token_usage", {})
        if meta:
            intent_usage = {
                "input_tokens":    meta.get("input_tokens")  or meta.get("prompt_tokens", 0),
                "output_tokens":   meta.get("output_tokens") or meta.get("completion_tokens", 0),
                "total_tokens":    meta.get("total_tokens", 0),
                "thinking_tokens": meta.get("output_token_details", {}).get("reasoning", 0),
            }
    except Exception:
        data = {}

    intent = data.get("intent", "other")
    product_type = data.get("product_type") or None
    if product_type == "null":
        product_type = None


    
    filters = data.get("filters", {})
    filters = {k: v for k, v in filters.items() if v is not None and v != "null"}
    vehicle_nn =   filters.get("vehicle_name") or None
    if vehicle_nn == "null":
        vehicle_nn = None

    print(product_type)


    # If vehicle_name exists but product_type is unknown, resolve from DB
    if not product_type and filters.get("vehicle_name"):
        found = get_vehicle_by_name(filters["vehicle_name"])
        if found and found[0].get("type"):
            vtype = found[0]["type"]
            if "اسكوتر" in vtype or "سكوتر" in vtype:
                product_type = "scooter"
            elif "خوذ" in vtype or "هيلم" in vtype:
                product_type = "helmet"
            else:
                product_type = "motorcycle"

    company_val = filters.get("company", "").lower().strip()

    # --- Company vs vehicle_name disambiguation ---
    if (not vehicle_nn
        and company_val
        and intent in ("details", "installment", "compare", "browse", "filter")):

        from dashboard_services.vehicle_query_services import get_company_vehicle_count
        if company_val in known_brands_set:
            # Known brand — but if it has only 1 vehicle, treat as specific vehicle lookup
            count = get_company_vehicle_count(company_val)
            if count == 1:
                found = get_vehicle_by_name(filters["company"])
                if found and found[0].get("type"):
                    v = found[0]
                    vtype = v["type"]
                    filters["vehicle_name"] = v["name_en"]
                    filters.pop("company", None)
                    intent = "details"
                    if "اسكوتر" in vtype or "سكوتر" in vtype:
                        product_type = "scooter"
                    elif "خوذ" in vtype or "هيلم" in vtype:
                        product_type = "helmet"
                    else:
                        product_type = "motorcycle"
            # else: multiple vehicles under this brand — keep as company filter (browse/filter)
        else:
            # NOT a known brand — maybe LLM confused a vehicle name for a company
            found = get_vehicle_by_name(filters["company"])
            if found and found[0].get("type"):
                v = found[0]
                vtype = v["type"]
                filters["vehicle_name"] = v["name_en"]
                filters.pop("company", None)
                intent = "details"
                if "اسكوتر" in vtype or "سكوتر" in vtype:
                    product_type = "scooter"
                elif "خوذ" in vtype or "هيلم" in vtype:
                    product_type = "helmet"
                else:
                    product_type = "motorcycle"

    lead_info = data.get("lead_info", {})
    existing_lead = state.get("lead", {})
    if lead_info.get("name"):
        existing_lead["name"] = lead_info["name"]
    if lead_info.get("phone"):
        existing_lead["phone"] = lead_info["phone"]
    if lead_info.get("booking_purpose"):
        existing_lead["booking_purpose"] = lead_info["booking_purpose"]
    if lead_info.get("appointment_date"):
        existing_lead["appointment_date"] = lead_info["appointment_date"]

    return {
        "intent": intent,
        "product_type": product_type,
        "filters": filters,
        "lead": existing_lead,
        "intent_usage": intent_usage,
        "ask_clarification": None,   # reset each turn; nodes set it if needed
    }
