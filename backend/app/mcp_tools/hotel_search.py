from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.mcp_tools.destination_resolver import resolve_destination
from app.mcp_tools.tool_parsing import first_nested_price


async def search_hotels(
    settings: Settings,
    destination: str,
    checkin: str,
    checkout: str,
    adults: int = 1,
) -> dict[str, Any]:
    """Search hotel rates through LiteAPI."""
    if not settings.liteapi_key:
        return {"provider": "LiteAPI Hotels", "mode": "not configured", "hotels": []}

    profile = await resolve_destination(settings, destination)
    body = {
        "checkin": checkin,
        "checkout": checkout,
        "currency": "USD",
        "guestNationality": "US",
        "occupancies": [{"adults": adults}],
        "cityName": profile["city"],
        "countryCode": profile["country"] or "US",
        "limit": 10,
        "includeHotelData": True,
    }

    try:
        async with httpx.AsyncClient(timeout=16) as client:
            response = await client.post(
                "https://api.liteapi.travel/v3.0/hotels/rates",
                json=body,
                headers={"X-API-Key": settings.liteapi_key},
            )
            if response.status_code == 204:
                return {"provider": "LiteAPI Hotels", "mode": "live", "hotels": []}
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        return {"provider": "LiteAPI Hotels", "mode": "error", "error": str(exc), "hotels": []}

    hotels = []
    raw_hotels = payload.get("data") or payload.get("hotels") or payload.get("results") or []
    for item in raw_hotels[:5]:
        if not isinstance(item, dict):
            continue

        hotel = item.get("hotel")
        if not isinstance(hotel, dict):
            hotel = {}

        hotels.append(
            {
                "name": item.get("name") or hotel.get("name") or "Hotel option",
                "price": first_nested_price(item),
                "currency": item.get("currency") or "USD",
                "address": item.get("address") or hotel.get("address"),
            }
        )

    return {"provider": "LiteAPI Hotels", "mode": "live", "city": profile["city"], "country": profile["country"], "hotels": hotels}
