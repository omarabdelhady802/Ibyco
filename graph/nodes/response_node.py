"""
Response Node: Gemini Flash (via OpenRouter) generates the final Arabic response.
"""
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from graph.state import AgentState
from llm.gemini import get_gemini
from dashboard_services.vehicle_query_services import _fmt_price, _safe, _has_value
from dashboard_services.client_services import ClientServices

_SHOWROOM = (
    "ibyco  motorcycles & accessories showroom | Alexandria, 12 St 302 off Bahaa El-Din El-Ghatoury, Smouha | "
    "Daily 2PM-11PM (Friday closed) | WhatsApp: 01505989502 / 01505989506"
)

SYSTEM_PROMPT = (
    f'You are a sales assistant at "ibyco" motorcycles & accessories showroom.\n'
    f"Reply in the SAME LANGUAGE the customer uses (Egyptian Arabic or English).\n"
    f"Be professional, friendly, and concise. Present data clearly.\n"
    f"NEVER hallucinate products — only use data provided.\n"
    f"End every reply with a short invitation to visit or contact us.\n"
    f"Oils/accessories are not in the catalog — direct to showroom.\n"
    f"{_SHOWROOM}"
)

BOOKING_PROMPT = (
    f'You are a sales assistant at "ibyco" showroom.\n'
    f"Reply in the SAME LANGUAGE the customer uses.\n"
    f"The customer wants to book a visit. If name/phone not provided yet, ask politely.\n"
    f"{_SHOWROOM}"
)

BOOKING_CONFIRMED_AR = (
    "تم استلام طلب حجزك بنجاح!\n"
    "سيتواصل معك فريق ibyco قريباً لتأكيد الموعد.\n\n"
    "يسعدنا خدمتك — للتواصل الفوري: 01505989502"
)
BOOKING_CONFIRMED_EN = (
    "Your booking request has been received!\n"
    "The ibyco team will contact you shortly to confirm.\n\n"
    "You can also reach us directly: 01505989502"
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
        parts.append(f"No {product_label} currently available matching these criteria.")

    if intent == "complaint":
        if state.get("complaint_saved"):
            parts.append("The customer's complaint has been received and logged successfully. They will be contacted shortly.")
        else:
            parts.append("The customer wants to file a complaint.")

    if intent == "booking":
        name = lead.get("name")
        phone = lead.get("phone")
        if name and phone:
            parts.append(f"Customer info: Name: {name}, Phone: {phone}")
        else:
            parts.append("The customer wants to book but hasn't provided their details yet.")

    return "\n".join(parts)


def _static_response(state: AgentState, text: str) -> dict:
    """Return a static reply without calling the LLM."""
    message = state["current_message"]
    history = state.get("conversation_history", [])
    updated_history = list(history) + [
        {"role": "user",      "content": message},
        {"role": "assistant", "content": text},
    ]
    try:
        ClientServices.update_client_turn(
            client=state.get("client"),
            user_message=message,
            bot_response=text,
        )
    except Exception:
        pass
    return {
        "response":             text,
        "conversation_history": updated_history,
        "usage":                state.get("intent_usage") or {},
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
    history = state.get("conversation_history", [])
    intent = state.get("intent", "other")

    try:
        context = _build_context(state)
    except Exception:
        import traceback
        traceback.print_exc()
        context = ""

    client = state.get("client")
    old_summary = client.chat_summary if client else ""
    filters = state.get("filters", {})
    lead = state.get("lead", {})

    sys_content = BOOKING_PROMPT if intent == "booking" else SYSTEM_PROMPT
    if context:
        sys_content += f"\n\nAvailable data:\n{context}"

    sys_content += f"""

---
CRM TASK: After writing your reply, append a section that updates the client summary.

EXISTING SUMMARY:
{old_summary or '(new client)'}

INTENT: {intent or 'unknown'}
FILTERS: {filters}
LEAD: {lead}

Format your full output EXACTLY like this:
<REPLY>
your reply to the customer here
</REPLY>
<SUMMARY>
updated merged summary here (max 500 chars, bullet points, English)
</SUMMARY>"""

    messages = [SystemMessage(content=sys_content)]

    for turn in history[-6:]:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))

    messages.append(HumanMessage(content=message))

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
        response_text = reply_match.group(1).strip() if reply_match else raw
        if summary_match:
            new_summary = summary_match.group(1).strip()[:2000]

        meta = getattr(result, "usage_metadata", None) or getattr(result, "response_metadata", {}).get("token_usage", {})
        if meta:
            usage = {
                "input_tokens":    meta.get("input_tokens")  or meta.get("prompt_tokens", 0),
                "output_tokens":   meta.get("output_tokens") or meta.get("completion_tokens", 0),
                "total_tokens":    meta.get("total_tokens", 0),
                "thinking_tokens": meta.get("output_token_details", {}).get("reasoning", 0),
            }
    except Exception as e:
        response_text = f"Sorry, an error occurred: {e}"

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

    updated_history = list(history) + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response_text},
    ]

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
        if lead.get("name") and lead.get("phone"):
            booking_stage = "confirmed"
        else:
            booking_stage = "collecting_info"

    return {
        "response": response_text,
        "conversation_history": updated_history,
        "booking_stage": booking_stage,
        "usage": usage,
    }
