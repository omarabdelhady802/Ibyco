"""
Compare Node: fetches both vehicles by name and stores them in state.
No LLM — deterministic lookup; Gemini in response_node does the comparison text.
"""
import math
from graph.state import AgentState
from dashboard_services.vehicle_query_services import get_vehicle_by_name


def _clean(v: dict) -> dict:
    return {
        k: (None if isinstance(val, float) and math.isnan(val) else val)
        for k, val in v.items()
    }


def _best_match(name: str, results: list) -> dict:
    """Pick the result whose English or Arabic name is closest to the query."""
    q = name.lower().strip()
    # Prefer exact substring match in english_name
    for r in results:
        en = (r.get("name_en") or "").lower()
        if q in en or en in q:
            return r
    # Then try arabic name
    for r in results:
        ar = r.get("name_ar") or ""
        if q in ar or name.strip() in ar:
            return r
    return results[0]


def compare_node(state: AgentState) -> dict:
    filters = state.get("filters", {})
    name1 = filters.get("vehicle_name", "")
    name2 = filters.get("vehicle_name_2", "")

    vehicles = []
    for name in (name1, name2):
        if name:
            found = get_vehicle_by_name(name)
            if found:
                vehicles.append(_clean(_best_match(name, found)))

    return {"vehicles": vehicles}
