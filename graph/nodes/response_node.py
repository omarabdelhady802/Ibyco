"""
Response Node: Gemini Flash (via OpenRouter) generates the final Arabic response.
"""
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState
from llm.gemini import get_gemini
from dashboard_services.vehicle_query_services import _fmt_price, _safe, _has_value
from dashboard_services.client_services import ClientServices

_SHOWROOM = (
    "ibyco  motorcycles & accessories showroom | Alexandria, 12 St 302 off Bahaa El-Din El-Ghatoury, Smouha | "
    "Daily 2PM-11PM (Friday closed) | Phone Numbers: 01147985063"
)

SYSTEM_PROMPT = (
    f'You are a sales assistant at "ibyco" motorcycles & accessories showroom.\n'
    f"Reply ONLY in Egyptian Arabic or English — NEVER mix in any other language.\n"
    f"Detect the language from the customer's message and reply entirely in that language.\n"
    f"Be professional, friendly, and concise. Present data clearly.\n"
    f"IMPORTANT: When showing a list of products, you MUST include EVERY product from the data — never skip or summarize. Show ALL of them.\n"
    f"NEVER hallucinate products — only use data provided.\n"
    f"Oils/accessories are not in the catalog — direct to showroom.\n"
    f"Showroom installment requirements papers and documents: صورة بطاقة المشتري + صورة بطاقة الضامن + إيصال.\n"
    f"When the customer shows interest (browsing, asking details, installment, or comparing), "
    f"naturally suggest booking a visit or test ride — e.g. 'تحب احجزلك معاد تيجي تشوفها؟' or 'عايز تيجي تجربها؟'\n"
    f"Don't force it every message — suggest it when it feels natural after showing product info.\n"
    f"{_SHOWROOM}"
)

BOOKING_PROMPT = (
    f'You are a sales assistant at "ibyco" showroom.\n'
    f"Reply ONLY in Egyptian Arabic or English — NEVER mix in any other language.\n"
    f"Detect the language from the customer's message and reply entirely in that language.\n"
    f"The customer wants to book a visit or test ride.\n"
    f"IMPORTANT: Friday (الجمعة) is a DAY OFF — the showroom is CLOSED on Fridays. "
    f"If the customer picks Friday, politely tell them it's closed and suggest Saturday or another day.\n"
    f"{_SHOWROOM}"
)

BOOKING_CONFIRMED_AR = (
    "تم استلام طلب حجزك بنجاح!\n"
    "سيتواصل معك فريق ibyco قريباً لتأكيد الموعد.\n\n"
    "يسعدنا خدمتك — للتواصل الفوري: 01147985063"
)
BOOKING_CONFIRMED_EN = (
    "Your booking request has been received!\n"
    "The ibyco team will contact you shortly to confirm.\n\n"
    "You can also reach us directly: 01147985063"
)


def _format_vehicle(v: dict) -> str:
    """Format a vehicle dict into readable text for the LLM context."""
    lines = [
        f"* {_safe(v.get('name_ar'))} ({_safe(v.get('name_en'))})",
        f"   Type: {_safe(v.get('type'))} | Color: {_safe(v.get('color'))}",
        f"   Brand: {_safe(v.get('company'))} | Agent: {_safe(v.get('agent'))}",
        f"   Price: {_fmt_price(v.get('price'))}",
    ]
    if v.get("engine_cc"):
        lines.append(
            f"   Engine: {_safe(v.get('engine_cc'))} | {_safe(v.get('engine_type'))} | {_safe(v.get('transmission'))}"
        )
    if _has_value(v.get("min_down")):
        lines.append(
            f"   Min down payment: {_fmt_price(v.get('min_down'))} | 12-month installment: {_fmt_price(v.get('installment_12'))}/month"
        )
    if v.get("notes"):
        lines.append(f"   Notes: {v['notes']}")
    return "\n".join(lines)


def _build_context(state: AgentState) -> str:
    intent = state.get("intent", "other")
    product_type = state.get("product_type") or "motorcycle"
    vehicles = state.get("vehicles", [])
    lead = state.get("lead", {})
    ask_clarification = state.get("ask_clarification")

    # Clarification needed before we can calculate
    if ask_clarification == "vehicle_name":
        return "The customer wants installment info but didn't specify the model. Ask them which model or product they want installment for."
    if ask_clarification == "vehicle_name1":
        return "The customer wants installment info but the model name wasn't found in the catalog. Apologize and ask them to clarify the model name."
    if ask_clarification == "down_payment":
        return "The customer wants installment info but didn't mention the down payment. Ask them how much down payment they will pay."

    product_label = {"motorcycle": "motorcycles", "scooter": "scooters", "helmet": "helmets"}.get(
        product_type, "products"
    )

    parts = []

    if intent == "compare":
        if vehicles:
            parts.append("The two products to compare:")
            for v in vehicles:
                parts.append(_format_vehicle(v))
            parts.append("Compare these two products in detail: price, engine, speed, installment, and features.")
        else:
            parts.append("Neither of the two products requested for comparison was found in the catalog.")
    elif intent == "installment" and vehicles and vehicles[0].get("monthly_payment") is not None:
        v = vehicles[0]
        parts.append(f"Installment options for {v.get('name_ar')} ({v.get('name_en')}):")
        parts.append(f"   Product price: {_fmt_price(v.get('price'))}")
        if v.get("down_payment"):
            parts.append(f"   Down payment: {_fmt_price(v.get('down_payment'))}")
        for plan in vehicles:
            if plan.get("monthly_payment") is not None:
                parts.append(f"   {plan['months']} months → {_fmt_price(plan['monthly_payment'])}/month")
    elif vehicles:
        parts.append(f"Available {product_label} matching the request:")
        for v in vehicles:
            parts.append(_format_vehicle(v))
    elif intent in ("browse", "filter", "details"):
        other_hint = state.get("other_types_hint")
        if other_hint:
            type_names = {"motorcycle": "موتوسيكلات (motorcycles)", "scooter": "اسكوترات (scooters)", "helmet": "خوذ (helmets)"}
            others = ", ".join(f"{other_hint[k]} {type_names.get(k, k)}" for k in other_hint)
            parts.append(
                f"No more {product_label} beyond what was already shown. "
                f"BUT we also have other products: {others}. "
                f"Suggest these to the customer — e.g. 'مفيش موتوسيكلات تانية، بس عندنا كمان اسكوترات، تحب تشوفهم؟'"
            )
        else:
            parts.append(f"No {product_label} currently available matching these criteria.")

    if intent == "complaint":
        if state.get("complaint_saved"):
            parts.append("The customer's complaint has been received and logged successfully. They will be contacted shortly.")
        else:
            parts.append("The customer wants to file a complaint.")

    if intent == "booking":
        if state.get("booking_saved"):
            date    = lead.get("appointment_date")
            purpose = lead.get("booking_purpose")
            parts.append(f"Booking has been saved successfully. Date: {date or 'not specified yet'}, Purpose: {purpose or 'showroom visit'}.")
            parts.append("Confirm to the customer that their booking is received and the team will contact them to confirm.")
        else:
            parts.append("The customer wants to book a visit/appointment but hasn't mentioned a date or time yet.")
            parts.append("Ask ONLY for the preferred date/time. Keep it short — ONE question only, don't repeat showroom info if already mentioned.")

    return "\n".join(parts)


def _static_response(state: AgentState, text: str) -> dict:
    """Return a static reply without calling the LLM."""
    message = state["current_message"]
    try:
        ClientServices.update_client_turn(
            client=state.get("client"),
            user_message=message,
            bot_response=text,
        )
    except Exception:
        pass
    return {
        "response": text,
        "usage":    state.get("intent_usage") or {},
    }


def response_node(state: AgentState) -> dict:
    # Booking confirmed — skip LLM, return static confirmation
    if state.get("booking_saved"):
        message = state.get("current_message", "")
        is_arabic = any("\u0600" <= c <= "\u06ff" for c in message)
        text = BOOKING_CONFIRMED_AR if is_arabic else BOOKING_CONFIRMED_EN
        return _static_response(state, text)

    llm = get_gemini()
    message = state["current_message"]
    intent = state.get("intent", "other")

    vehicles = state.get("vehicles", [])
    print(
        f"\n── Debug: response_node input ─────────────────\n"
        f"  Intent: {intent} | Product type: {state.get('product_type')}\n"
        f"  Filters: {state.get('filters', {})}\n"
        f"  Vehicles ({len(vehicles)}):"
    )
    for i, v in enumerate(vehicles):
        print(f"    [{i+1}] {v.get('name_en', v.get('name_ar', '?'))} — {v.get('type', '?')} — {v.get('price', '?')}")
    print(f"  Total count: {state.get('total_count')}")
    print(f"  Ask clarification: {state.get('ask_clarification')}")
    print(f"───────────────────────────────────────────────")

    try:
        context = _build_context(state)
    except Exception:
        import traceback
        traceback.print_exc()
        context = ""

    client = state.get("client")
    old_summary    = (client.chat_summary   or "") if client else ""
    last_bot_reply = (client.last_bot_reply or "") if client else ""
    filters = state.get("filters", {})
    lead = state.get("lead", {})

    sys_content = BOOKING_PROMPT if intent == "booking" else SYSTEM_PROMPT

    # For greetings, keep it clean — don't push old vehicle context
    if intent == "greeting":
        sys_content += "\n\nThe customer is greeting you. Reply with a warm greeting and ask how you can help. Do NOT mention any specific products or previous conversations."
    else:
        # Give the LLM client context so it can personalise the reply
        if old_summary:
            sys_content += f"\n\nClient history summary:\n{old_summary}"
        if last_bot_reply:
            sys_content += f"\nYour last reply to this client:\n{last_bot_reply}"

        if context:
            sys_content += f"\n\nAvailable data:\n{context}"

    sys_content += f"""

---
CRM TASK: After writing your reply, append an updated client state snapshot.

RULES FOR THE SUMMARY:
- This summary is used by the AI in the NEXT turn to understand the conversation state.
- REPLACE the old summary entirely — do NOT append to it or repeat old content.
- Write it as a single clean paragraph, max 1000 chars, in English.
- KEEP all existing context (customer name, phone, preferences, previous interests).
- When new data arrives (new vehicle name, new filters, new browse results), UPDATE those fields — replace old values with new ones, don't remove unrelated context.
- If the customer asks about a new vehicle or browses again, update the vehicle/filter fields but keep customer info and other context.
- Always mention these if known: intent, product type, vehicle name(s), down payment, months, budget, brand, customer name, customer phone, booking purpose, appointment date, what the bot last asked the customer.
- If the current intent is 'other' or 'greeting', preserve all previous context as-is.
 

EXISTING SUMMARY :
{old_summary or '(new client)'}

CURRENT TURN:
INTENT: {intent or 'unknown'}
FILTERS: {filters}
LEAD: {lead}

Format your full output EXACTLY like this:
<REPLY>
your reply to the customer here
</REPLY>
<SUMMARY>
updated paragraph snapshot here
</SUMMARY>"""



    messages = [
        SystemMessage(content=sys_content),
        HumanMessage(content=message),
    ]

    # Gemini 2.0 Flash pricing via OpenRouter
    _INPUT_COST_PER_M  = 0.10   # $ per 1M input tokens
    _OUTPUT_COST_PER_M = 0.40   # $ per 1M output tokens

    usage = {}
    new_summary = old_summary
    try:
        result = llm.invoke(messages)
        raw = result.content.strip()

        # Parse <REPLY> and <SUMMARY> blocks
        import re
        reply_match   = re.search(r"<REPLY>(.*?)</REPLY>", raw, re.DOTALL)
        summary_match = re.search(r"<SUMMARY>(.*?)</SUMMARY>", raw, re.DOTALL)
        if reply_match:
            response_text = reply_match.group(1).strip()
        else:
            # LLM skipped or misspelled tags — strip everything after <SUMMARY> and any XML-like tags
            response_text = re.sub(r"<SUMMARY>.*", "", raw, flags=re.DOTALL).strip()
            response_text = re.sub(r"</?[A-Z][A-Z_]*>", "", response_text).strip()
        if summary_match:
            new_summary = summary_match.group(1).strip()
        # Final safety: remove any leaked tags from the customer-facing response
        response_text = re.sub(r"</?[A-Z][A-Z_]*>", "", response_text).strip()

        meta = getattr(result, "usage_metadata", None) or getattr(result, "response_metadata", {}).get("token_usage", {})
        if meta:
            usage = {
                "input_tokens":    meta.get("input_tokens")  or meta.get("prompt_tokens", 0),
                "output_tokens":   meta.get("output_tokens") or meta.get("completion_tokens", 0),
                "total_tokens":    meta.get("total_tokens", 0),
                "thinking_tokens": meta.get("output_token_details", {}).get("reasoning", 0),
            }
    except Exception as e:
        print(f"[ERROR] response_node LLM call failed: {e}")
        response_text = None
    # Aggregate intent + response tokens and compute cost
    intent_usage = state.get("intent_usage") or {}
    total_input    = (intent_usage.get("input_tokens", 0)    + usage.get("input_tokens", 0))
    total_output   = (intent_usage.get("output_tokens", 0)   + usage.get("output_tokens", 0))
    total_thinking = (intent_usage.get("thinking_tokens", 0) + usage.get("thinking_tokens", 0))
    total_all      = total_input + total_output
    cost_usd = (total_input * _INPUT_COST_PER_M + total_output * _OUTPUT_COST_PER_M) / 1_000_000

    print(
        f"\n── Token usage ──────────────────────────────\n"
        f"  Intent node  → in: {intent_usage.get('input_tokens', 0):>6} | "
        f"out: {intent_usage.get('output_tokens', 0):>5} | "
        f"think: {intent_usage.get('thinking_tokens', 0):>5}\n"
        f"  Response node→ in: {usage.get('input_tokens', 0):>6} | "
        f"out: {usage.get('output_tokens', 0):>5} | "
        f"think: {usage.get('thinking_tokens', 0):>5}\n"
        f"  TOTAL        → in: {total_input:>6} | out: {total_output:>5} | "
        f"think: {total_thinking:>5} | all: {total_all:>6}\n"
        f"  Cost         → ${cost_usd:.6f}\n"
        f"─────────────────────────────────────────────"
    )

    usage["intent_input_tokens"]    = intent_usage.get("input_tokens", 0)
    usage["intent_output_tokens"]   = intent_usage.get("output_tokens", 0)
    usage["intent_thinking_tokens"] = intent_usage.get("thinking_tokens", 0)
    usage["total_all_tokens"]       = total_all
    usage["cost_usd"]               = round(cost_usd, 6)

    # Persist turn to DB — summary already generated above, no extra LLM call
    try:
        ClientServices.update_client_turn(
            client=state.get("client"),
            user_message=message,
            bot_response=response_text,
            new_summary=new_summary,
        )
    except Exception:
        pass  # never crash the response over a DB write

    booking_stage = state.get("booking_stage")
    lead = state.get("lead", {})
    if intent == "booking":
        if state.get("booking_saved"):
            booking_stage = "confirmed"
        else:
            booking_stage = "collecting_info"

    return {
        "response":      response_text,
        "booking_stage": booking_stage,
        "usage":         usage,
    }
