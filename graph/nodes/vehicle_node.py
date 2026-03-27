"""
Vehicle Node: unified handler for motorcycles, scooters (and future types).
Replaces the separate motorcycle_node and scooter_node.
product_type is used as a DB *filter*, NOT a routing gate — so a wrong
or missing product_type never blocks finding the right vehicle.
"""
import json
from graph.state import AgentState
from dashboard_services.vehicle_query_services import (
    get_price_spread,
    get_vehicle_by_name,
    get_vehicles,
    calculate_custom_installment,
    get_similar_vehicles,
    get_total_count,
)
from tools.vehicle_tools import search_vehicles, vehicle_by_monthly_budget

# Map product_type → Arabic DB type string used in Motors.moto_type
_TYPE_MAP = {
    "motorcycle": "موتوسيكل",
    "scooter":    "اسكوتر",
}

PAGE_SIZE = 4


def vehicle_node(state: AgentState) -> dict:
    intent = state.get("intent", "browse")
    filters = state.get("filters", {})
    product_type = state.get("product_type")  # motorcycle | scooter | None

    vehicles = []
    ask_clarification = None
    show_more = filters.get("show_more", False)

    # When filtering by company/brand, show ALL vehicle types from that brand
    # (e.g. Keeway has both scooters and motorcycles)
    if filters.get("company"):
        db_type = None
    else:
        db_type = _TYPE_MAP.get(product_type)  # None when product_type is unknown

    def _resolve_name(filters: dict) -> str:
        parts = [filters.get("company", ""), filters.get("vehicle_name", "")]
        return " ".join(p for p in parts if p).strip()

    # Total count for the type (or all vehicles if type unknown)
    total_count = get_total_count({"type": db_type} if db_type else {})

    # --- Installment without vehicle name or budget → ask which vehicle ---
    if intent == "installment" and not filters.get("vehicle_name") and not filters.get("max_installment_12"):
        ask_clarification = "vehicle_name"
        return {"vehicles": [], "ask_clarification": ask_clarification, "total_count": total_count}

    # --- Vehicle name provided → always try name lookup first (type-agnostic) ---
    if filters.get("vehicle_name") and intent in ("details", "browse", "filter"):
        name = _resolve_name(filters)
        v = get_vehicle_by_name(name)
        if v:
            vehicles = [v] + get_similar_vehicles(v, count=3)
            return {"vehicles": vehicles, "ask_clarification": ask_clarification, "total_count": total_count}

    # ----- Intent handlers -----

    if intent == "details":
        name = _resolve_name(filters)
        v = get_vehicle_by_name(name)
        if v:
            vehicles = [v] + get_similar_vehicles(v, count=3)

    elif intent == "installment" and filters.get("vehicle_name"):
        name = _resolve_name(filters)
        v = get_vehicle_by_name(name)
        if not v:
            ask_clarification = "vehicle_name1"
            return {"vehicles": [], "ask_clarification": ask_clarification, "total_count": total_count}
        if "down_payment" not in filters:
            ask_clarification = "down_payment"
            return {"vehicles": [], "ask_clarification": ask_clarification, "total_count": total_count}

        months = filters.get("months")
        down_payment = filters.get("down_payment", 0)
        if months and v:
            months = int(months)
            calc = calculate_custom_installment(v, months, down_payment=down_payment)
            vehicles = [calc]
        elif v:
            vehicles = [
                c for m in (6, 12, 18, 24)
                for c in [calculate_custom_installment(v, m, down_payment=down_payment)]
                if "error" not in c
            ]

    elif intent == "installment" and filters.get("max_installment_12"):
        raw = vehicle_by_monthly_budget.invoke({
            "max_monthly": filters["max_installment_12"],
            "months": 12,
            "vehicle_type": db_type,
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
            raw = search_vehicles.invoke({
                "max_price": filters.get("max_price"),
                "min_price": filters.get("min_price"),
                "company": filters.get("company"),
                "transmission": filters.get("transmission"),
                "vehicle_type": db_type,
                "limit": PAGE_SIZE,
            })
            vehicles = json.loads(raw)
        else:
            offset = PAGE_SIZE if show_more else 0
            type_filter = {"type": db_type} if db_type else {}
            vehicles = get_price_spread(type_filter, count=PAGE_SIZE, offset=offset)

    else:
        # browse
        offset = PAGE_SIZE if show_more else 0
        type_filter = {"type": db_type} if db_type else {}
        vehicles = get_price_spread(type_filter, count=PAGE_SIZE, offset=offset)

    # When show_more returns nothing (or browse with no results), tell response about ALL other available types
    other_types_hint = None
    if show_more and not vehicles:
        other_counts = {}
        for key, ar_type in _TYPE_MAP.items():
            if ar_type != db_type:
                cnt = get_total_count({"type": ar_type})
                if cnt > 0:
                    other_counts[key] = cnt
        # Also count helmets
        helmet_count = get_total_count({"type": "خوذ"})
        if helmet_count > 0:
            other_counts["helmet"] = helmet_count
        if other_counts:
            other_types_hint = other_counts

    return {
        "vehicles": vehicles,
        "ask_clarification": ask_clarification,
        "total_count": total_count,
        "other_types_hint": other_types_hint,
    }
