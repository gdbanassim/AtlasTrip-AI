from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.mcp_tools.destination_resolver import is_airport_code, resolve_destination


async def search_flights(
    settings: Settings,
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    max_price: int | None = None,
) -> dict[str, Any]:
    """Search real flight prices through SerpApi Google Flights."""
    if not settings.serpapi_api_key:
        return {"provider": "SerpApi Google Flights", "mode": "not configured", "offers": []}

    origin_profile = await resolve_destination(settings, origin) if not is_airport_code(origin) else {"airport": origin.upper()}
    destination_profile = await resolve_destination(settings, destination)
    params: dict[str, Any] = {
        "engine": "google_flights",
        "api_key": settings.serpapi_api_key,
        "departure_id": origin_profile["airport"],
        "arrival_id": destination_profile["airport"],
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "USD",
        "hl": "en",
        "gl": "us",
        "travel_class": 1,
    }
    if max_price:
        params["max_price"] = max_price

    try:
        async with httpx.AsyncClient(timeout=18) as client:
            response = await client.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        return {"provider": "SerpApi Google Flights", "mode": "error", "error": str(exc), "offers": []}

    offers = []
    for item in (payload.get("best_flights") or payload.get("other_flights") or [])[:5]:
        first_leg = (item.get("flights") or [{}])[0]
        offers.append(
            {
                "price": item.get("price"),
                "airline": first_leg.get("airline", "Unknown airline"),
                "duration": item.get("total_duration") or first_leg.get("duration"),
                "stops": max(len(item.get("flights") or []) - 1, 0),
                "booking_token": item.get("booking_token"),
            }
        )

    return {
        "provider": "SerpApi Google Flights",
        "mode": "live",
        "arrival_airport": destination_profile["airport"],
        "arrival_city": destination_profile["city"],
        "offers": offers,
    }
