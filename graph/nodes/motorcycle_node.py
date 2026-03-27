"""
Motorcycle Node: calls motorcycle tools and stores results in state.
No LLM — deterministic data fetching based on intent + filters.
"""
import json
from graph.state import AgentState
from dashboard_services.vehicle_query_services import get_price_spread, get_vehicle_by_name, calculate_custom_installment, get_similar_vehicles, get_total_count
from tools.motorcycle_tools import (
    search_motorcycles,
    motorcycle_by_monthly_budget,
)

MOTO_TYPE = "موتوسيكل"


def motorcycle_node(state: AgentState) -> dict:
    intent = state.get("intent", "browse")
    filters = state.get("filters", {})

    vehicles = []
    ask_clarification = None
    show_more = filters.get("show_more", False)
    PAGE_SIZE = 5

    def _resolve_name(filters: dict) -> str:
        """Combine company + vehicle_name for a richer search query."""
        parts = [filters.get("company", ""), filters.get("vehicle_name", "")]
        return " ".join(p for p in parts if p).strip()

    total_count = get_total_count({"type": MOTO_TYPE})

    if intent == "installment" and not filters.get("vehicle_name") and not filters.get("max_installment_12"):
        ask_clarification = "vehicle_name"
        return {"vehicles": [], "ask_clarification": ask_clarification, "total_count": total_count}

    # If a vehicle name is provided, always try to find it first (handles wrong routing)
    if filters.get("vehicle_name") and intent in ("details", "browse", "filter"):
        name = _resolve_name(filters)
        v = get_vehicle_by_name(name)
        if v:
            vehicles = [v] + get_similar_vehicles(v, count=3)
            return {"vehicles": vehicles, "ask_clarification": ask_clarification, "total_count": total_count}

    if intent == "details":
        name = _resolve_name(filters)
        v = get_vehicle_by_name(name)
        if v:
            vehicles = [v] + get_similar_vehicles(v, count=3)

    elif intent == "installment" and filters.get("vehicle_name"):
        # First check if the vehicle actually exists before asking for down payment
        name = _resolve_name(filters)
        v = get_vehicle_by_name(name)
        if not v:
            ask_clarification = "vehicle_name1"
            return {"vehicles": [], "ask_clarification": ask_clarification}
        if "down_payment" not in filters:
            ask_clarification = "down_payment"
            return {"vehicles": [], "ask_clarification": ask_clarification}
        months = filters.get("months")
        name   = _resolve_name(filters)
        v = get_vehicle_by_name(name)
        down_payment = filters.get("down_payment", 0)
        if months and v:
            months = int(months)
            calc = calculate_custom_installment(v, months, down_payment=down_payment)
            vehicles = [calc]
        elif v:
            # No specific months — show all standard plans with the actual down_payment
            vehicles = [
                c for m in (6, 12, 18, 24)
                for c in [calculate_custom_installment(v, m, down_payment=down_payment)]
                if "error" not in c
            ]

    elif intent == "installment" and filters.get("max_installment_12"):
        raw = motorcycle_by_monthly_budget.invoke({
            "max_monthly": filters["max_installment_12"],
            "months": 12,
        })
        vehicles = json.loads(raw)
        if vehicles:
            seen = {v.get("name_en") for v in vehicles}
            for extra in get_similar_vehicles(vehicles[0], count=3):
                if extra.get("name_en") not in seen:
                    vehicles.append(extra)
                    seen.add(extra.get("name_en"))

    elif intent == "filter":
        has_filters = any(
            filters.get(k)
            for k in ("max_price", "min_price", "company", "transmission",
                      "max_installment_12", "max_installment_6",
                      "max_installment_18", "max_installment_24")
        )
        if has_filters:
            raw = search_motorcycles.invoke({
                "max_price": filters.get("max_price"),
                "min_price": filters.get("min_price"),
                "company": filters.get("company"),
                "transmission": filters.get("transmission"),
                "limit": PAGE_SIZE,
            })
            vehicles = json.loads(raw)
        else:
            # No actual filter values — treat as browse (price spread)
            offset = PAGE_SIZE if show_more else 0
            vehicles = get_price_spread({"type": MOTO_TYPE}, count=PAGE_SIZE, offset=offset)

    else:
        # browse — return a price-spread sample so different price points are visible
        offset = PAGE_SIZE if show_more else 0
        vehicles = get_price_spread({"type": MOTO_TYPE}, count=PAGE_SIZE, offset=offset)

    return {"vehicles": vehicles, "ask_clarification": ask_clarification, "total_count": total_count}
