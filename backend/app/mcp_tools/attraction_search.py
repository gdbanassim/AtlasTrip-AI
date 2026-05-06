from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.mcp_tools.destination_resolver import resolve_destination


async def find_attractions(settings: Settings, destination: str, interests: list[str]) -> dict[str, Any]:
    """Find nearby attractions through OpenTripMap."""
    if not settings.opentripmap_api_key:
        return {"provider": "OpenTripMap", "mode": "not configured", "places": []}

    profile = await resolve_destination(settings, destination)
    params = {
        "radius": 8000,
        "lon": profile["lon"],
        "lat": profile["lat"],
        "format": "json",
        "limit": 12,
        "apikey": settings.opentripmap_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://api.opentripmap.com/0.1/en/places/radius", params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        return {"provider": "OpenTripMap", "mode": "error", "error": str(exc), "places": []}

    places = [
        {"name": place.get("name"), "kinds": place.get("kinds"), "distance": place.get("dist")}
        for place in payload
        if place.get("name")
    ]
    return {"provider": "OpenTripMap", "mode": "live", "city": profile["city"], "country": profile["country"], "places": places[:8], "interests": interests}
