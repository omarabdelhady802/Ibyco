"""
Helmet Node: fetches helmets from the helmets table and stores results in state.
"""
from graph.state import AgentState
from models.models import db, Helmets


def _helmet_to_dict(h: Helmets) -> dict:
    return {
        "name_en":    h.english_name,
        "name_ar":    h.arabic_name,
        "company":    h.company,
        "price":      h.price,
        "type":       h.helmet_type,
        "color":      h.colors,
        "notes":      h.notes,
        "available":  h.is_available,
        "condition":  h.status,
        "img_url":    h.img_url,
    }


def helmet_node(state: AgentState) -> dict:
    intent = state.get("intent", "browse")
    filters = state.get("filters", {})

    query = Helmets.query.filter(Helmets.is_available == True)

    if filters.get("company"):
        query = query.filter(Helmets.company.ilike(f"%{filters['company']}%"))
    if filters.get("max_price"):
        query = query.filter(Helmets.price <= float(filters["max_price"]))
    if filters.get("min_price"):
        query = query.filter(Helmets.price >= float(filters["min_price"]))

    if intent == "details" and filters.get("vehicle_name"):
        name = filters["vehicle_name"].lower().strip()
        query = query.filter(
            (Helmets.english_name.ilike(f"%{name}%"))
            | (Helmets.arabic_name.ilike(f"%{name}%"))
        )

    rows = query.order_by(Helmets.price.asc()).limit(10).all()
    vehicles = [_helmet_to_dict(r) for r in rows]

    print(f"\n── Debug: helmet_node ──────────────────────")
    print(f"  Intent: {intent} | Filters: {filters}")
    print(f"  Helmets found: {len(vehicles)}")
    for v in vehicles:
        print(f"    {v.get('name_en')} | {v.get('type')} | {v.get('price')}")
    print(f"───────────────────────────────────────────")

    return {"vehicles": vehicles}
