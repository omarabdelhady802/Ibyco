import re
import math
from typing import Optional, List

from sqlalchemy import func
from models.database import Session
from models.models import Motors


def _get_session():
    return Session()


def _motor_to_dict(motor: Motors) -> dict:
    return {
        "name_en":       motor.english_name,
        "name_ar":       motor.arabic_name,
        "company":       motor.company,
        "agent":         motor.agency_name,
        "type":          motor.moto_type,
        "price":         motor.price,
        "engine_cc":     motor.engin_capacity,
        "engine_type":   motor.engin_type,
        "transmission":  motor.transmission_type,
        "max_speed":     motor.max_speed,
        "fuel_capacity": motor.fule_capacity,
        "brakes":        motor.brake_type,
        "notes":         motor.notes,
        "color":         motor.colors,
        "available":     motor.is_available,
        "condition":     motor.status,
        "img_url":       motor.img_url,
    }


# ---------------------------------------------------------------------------
# Vehicle queries
# ---------------------------------------------------------------------------

def get_vehicles(
    filters: dict = None,
    limit: int = 6,
    sort_by: str = None,
    ascending: bool = True,
) -> List[dict]:
    session = _get_session()
    query = session.query(Motors).filter(Motors.is_available == True)

    if filters:
        if filters.get("type"):
            query = query.filter(Motors.moto_type.ilike(f"%{filters['type']}%"))
        if filters.get("max_price"):
            query = query.filter(Motors.price <= float(filters["max_price"]))
        if filters.get("min_price"):
            query = query.filter(Motors.price >= float(filters["min_price"]))
        if filters.get("company"):
            query = query.filter(Motors.company.ilike(f"%{filters['company']}%"))
        if filters.get("transmission"):
            query = query.filter(Motors.transmission_type.ilike(f"%{filters['transmission']}%"))
        if filters.get("condition"):
            query = query.filter(Motors.status.ilike(f"%{filters['condition']}%"))

    col_map = {"price": Motors.price, "engine_cc": Motors.engin_capacity}
    if sort_by and sort_by in col_map:
        col = col_map[sort_by]
        query = query.order_by(col.asc() if ascending else col.desc())

    rows = query.limit(limit).all()
    return [_motor_to_dict(r) for r in rows]


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9\u0600-\u06ff]", "", s.lower())


def get_vehicle_by_name(name: str) -> Optional[dict]:
    """Four-tier search (case-insensitive):
    1. SQL LIKE — consecutive substring in English or Arabic name.
    2. ALL query words are whole tokens in English name + company (exact multi-word match).
    3. MAJORITY (>=2/3) of words match across English + Arabic + company tokens.
    4. Normalized match (strip punctuation/spaces then substring check).
    """
    session = _get_session()
    q = name.lower().strip()

    # Tier 1 — SQL LIKE
    row = (
        session.query(Motors)
        .filter(
            (func.lower(Motors.english_name).like(f"%{q}%"))
            | (Motors.arabic_name.like(f"%{name.strip()}%"))
        )
        .first()
    )
    if row:
        return _motor_to_dict(row)

    # Tiers 2-4 load all rows once
    all_rows = session.query(Motors).all()

    words = q.split()
    if words:
        def _all_tokens(m):
            return (
                set(re.split(r'\W+', str(m.english_name).lower()))
                | set(re.split(r'\W+', str(m.arabic_name)))
                | set(re.split(r'\W+', str(m.company).lower()))
            )

        # Tier 2 — ALL words match (precise)
        for m in all_rows:
            if all(w in _all_tokens(m) for w in words):
                return _motor_to_dict(m)

        # Tier 3 — MAJORITY match (>=2/3)
        threshold = max(1, math.ceil(len(words) * 2 / 3))
        for m in all_rows:
            toks = _all_tokens(m)
            if sum(1 for w in words if w in toks) >= threshold:
                return _motor_to_dict(m)

    # Tier 4 — normalized substring
    q_norm = _normalize(q)
    if q_norm:
        for m in all_rows:
            if q_norm in _normalize(str(m.english_name)):
                return _motor_to_dict(m)

    return None


def get_catalog_summary() -> dict:
    session = _get_session()
    rows = session.query(Motors).filter(Motors.is_available == True).all()

    types = {}
    companies = {}
    prices = []
    for r in rows:
        types[r.moto_type] = types.get(r.moto_type, 0) + 1
        companies[r.company] = companies.get(r.company, 0) + 1
        if r.price is not None:
            prices.append(r.price)

    return {
        "total":     len(rows),
        "types":     types,
        "companies": companies,
        "price_min": min(prices) if prices else 0,
        "price_max": max(prices) if prices else 0,
    }


def get_price_spread(filters: dict = None, count: int = 5) -> List[dict]:
    """Return `count` vehicles evenly spread across the price range."""
    session = _get_session()
    query = session.query(Motors).filter(Motors.is_available == True, Motors.price.isnot(None))

    if filters:
        if filters.get("type"):
            query = query.filter(Motors.moto_type.ilike(f"%{filters['type']}%"))
        if filters.get("company"):
            query = query.filter(Motors.company.ilike(f"%{filters['company']}%"))
        if filters.get("max_price") is not None:
            query = query.filter(Motors.price <= float(filters["max_price"]))
        if filters.get("min_price") is not None:
            query = query.filter(Motors.price >= float(filters["min_price"]))

    rows = query.order_by(Motors.price).all()

    if not rows:
        return []
    if len(rows) <= count:
        return [_motor_to_dict(r) for r in rows]

    step = (len(rows) - 1) / (count - 1)
    indices = sorted({round(i * step) for i in range(count)})
    return [_motor_to_dict(rows[i]) for i in indices]


def get_similar_vehicles(vehicle: dict, count: int = 3) -> List[dict]:
    """Return up to `count` vehicles of the same type within +/-40% of the given price."""
    price = vehicle.get("price")
    vtype = vehicle.get("type")
    name_en = vehicle.get("name_en", "")
    if not price or not vtype:
        return []

    session = _get_session()
    rows = (
        session.query(Motors)
        .filter(
            Motors.is_available == True,
            Motors.price.isnot(None),
            Motors.moto_type.ilike(f"%{vtype}%"),
            Motors.price.between(price * 0.6, price * 1.4),
            func.lower(Motors.english_name) != name_en.lower(),
        )
        .order_by(func.abs(Motors.price - price))
        .limit(count)
        .all()
    )
    return [_motor_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Installment calculation
# ---------------------------------------------------------------------------

def calculate_custom_installment(vehicle: dict, months: int, down_payment: float = 0) -> dict:
    """Calculate monthly installment using the range-based instalments table."""
    from services.db_service import get_installment_rate

    price = vehicle.get("price")
    name_en = vehicle.get("name_en") or ""

    if not price:
        return {"error": "Product price not available", "name_ar": vehicle.get("name_ar"), "name_en": name_en}

    down_pct = (down_payment / price * 100) if down_payment and price else 0
    rate_data = get_installment_rate(months, down_pct)

    if not rate_data:
        return {
            "error": "No installment plan available for this option",
            "name_ar": vehicle.get("name_ar"),
            "name_en": name_en,
        }

    monthly_rate_pct = rate_data["percentage_per_month"]
    financed_amount = price - down_payment
    total_interest = financed_amount * monthly_rate_pct / 100 * months
    total_repayment = price + total_interest
    monthly_payment = (financed_amount + total_interest) / months

    return {
        "name_ar":           vehicle.get("name_ar"),
        "name_en":           name_en,
        "price":             price,
        "down_payment":      round(down_payment),
        "financed_amount":   round(financed_amount),
        "months":            months,
        "interest_rate_pct": round(monthly_rate_pct * months, 2),
        "total_interest":    round(total_interest),
        "total_repayment":   round(total_repayment),
        "monthly_payment":   round(monthly_payment),
    }


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_price(val) -> str:
    try:
        return f"{int(val):,} EGP"
    except (ValueError, TypeError):
        return "N/A"


def _safe(val, default="N/A") -> str:
    if val is None:
        return default
    try:
        if math.isnan(float(val)):
            return default
    except (TypeError, ValueError):
        pass
    return str(val)


def _has_value(val) -> bool:
    if val is None:
        return False
    try:
        return not math.isnan(float(val))
    except (TypeError, ValueError):
        return bool(val)


def format_vehicle_arabic(v: dict) -> str:
    lines = [
        f"* {_safe(v.get('name_ar'))} ({_safe(v.get('name_en'))})",
        f"   Brand: {_safe(v.get('company'))} | Agent: {_safe(v.get('agent'))}",
        f"   Type: {_safe(v.get('type'))} | Color: {_safe(v.get('color'))}",
        f"   Price: {_fmt_price(v.get('price'))}",
        f"   Engine: {_safe(v.get('engine_cc'))} | {_safe(v.get('engine_type'))} | {_safe(v.get('transmission'))}",
        f"   Max speed: {_safe(v.get('max_speed'))}",
    ]
    if _has_value(v.get("notes")):
        lines.append(f"   Notes: {v['notes']}")
    return "\n".join(lines)
