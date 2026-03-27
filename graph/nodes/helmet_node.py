"""
Helmet Node: fetches helmets from DB and stores results in state.
"""
from graph.state import AgentState
from dashboard_services.vehicle_query_services import get_vehicles, get_vehicle_by_name

HELMET_TYPE = "خوذ"


def helmet_node(state: AgentState) -> dict:
    intent = state.get("intent", "browse")
    filters = state.get("filters", {})

    vehicles = []
    db_filters = {"type": HELMET_TYPE}

    if filters.get("company"):
        db_filters["company"] = filters["company"]
    if filters.get("max_price"):
        db_filters["max_price"] = filters["max_price"]
    if filters.get("min_price"):
        db_filters["min_price"] = filters["min_price"]

    if intent == "details" and filters.get("vehicle_name"):
        found = get_vehicle_by_name(filters["vehicle_name"])
        vehicles = [v for v in found if "خوذ" in (v.get("type") or "")]
    else:
        vehicles = get_vehicles(db_filters, limit=5, sort_by="price")

    print(f"\n── Debug: helmet_node ──────────────────────")
    print(f"  DB filters: {db_filters}")
    print(f"  Vehicles found: {len(vehicles)}")
    for v in vehicles:
        print(f"    {v.get('name_en')} | {v.get('type')} | {v.get('price')}")
    print(f"───────────────────────────────────────────")

    return {"vehicles": vehicles}
