from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def default_trip_dates(days: int) -> tuple[str, str]:
    start = date.today() + timedelta(days=45)
    end = start + timedelta(days=max(days - 1, 1))
    return start.isoformat(), end.isoformat()


def safe_int(value: Any) -> int | None:
    try:
        return round(float(value))
    except (TypeError, ValueError):
        return None


def first_nested_price(item: dict[str, Any] | None) -> int | None:
    if not isinstance(item, dict):
        return None

    for key in ("price", "total", "amount", "totalAmount", "minRate"):
        value = item.get(key)
        if isinstance(value, dict):
            value = value.get("amount") or value.get("value")
        parsed = safe_int(value)
        if parsed:
            return parsed

    rates = item.get("rates") or item.get("rooms") or []
    for rate in rates:
        if isinstance(rate, dict):
            parsed = first_nested_price(rate)
            if parsed:
                return parsed

    return None
