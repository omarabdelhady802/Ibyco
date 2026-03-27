"""
Unified vehicle tools — replaces motorcycle_tools + scooter_tools.
vehicle_type is an optional filter, not a hard gate.
"""
import json
from typing import Optional
from langchain_core.tools import tool
from dashboard_services.vehicle_query_services import (
    get_vehicles,
    get_vehicle_by_name,
    get_catalog_summary,
    calculate_custom_installment,
)


def _to_json(vehicles: list) -> str:
    return json.dumps(vehicles, ensure_ascii=False, default=str)


@tool
def search_vehicles(
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    company: Optional[str] = None,
    transmission: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    limit: int = 5,
) -> str:
    """Search available vehicles by filters. vehicle_type is the Arabic DB type (e.g. 'موتوسيكل', 'اسكوتر') or None for all."""
    filters = {}
    if vehicle_type:
        filters["type"] = vehicle_type
    if max_price:
        filters["max_price"] = max_price
    if min_price:
        filters["min_price"] = min_price
    if company:
        filters["company"] = company
    if transmission:
        filters["transmission"] = transmission
    return _to_json(get_vehicles(filters, limit=limit))


@tool
def vehicle_details(vehicle_name: str) -> str:
    """Get full details of a specific vehicle by name. Returns a JSON object."""
    found = get_vehicle_by_name(vehicle_name)
    if not found:
        return json.dumps({"error": "الموديل غير متوفر"}, ensure_ascii=False)
    return _to_json(found)


@tool
def vehicle_by_monthly_budget(
    max_monthly: float,
    months: int = 12,
    vehicle_type: Optional[str] = None,
    limit: int = 3,
) -> str:
    """Find vehicles that fit a monthly installment budget. Returns JSON."""
    from dashboard_services.instalment_services import InstalmentServices
    rate_data = InstalmentServices.get_installment_rate(months, 0)
    if not rate_data:
        return json.dumps({"error": "لا تتوفر بيانات تقسيط لهذه المدة"}, ensure_ascii=False)

    rate = rate_data["percentage_per_month"]
    max_price = max_monthly * months / (1 + rate / 100 * months)
    filters = {"max_price": max_price}
    if vehicle_type:
        filters["type"] = vehicle_type
    return _to_json(get_vehicles(filters, limit=limit, sort_by="price", ascending=True))
