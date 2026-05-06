from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.mcp_tools.destination_resolver import resolve_destination


async def get_weather(settings: Settings, destination: str, days: int) -> dict[str, Any]:
    """Get daily weather from Open-Meteo."""
    profile = await resolve_destination(settings, destination)
    params = {
        "latitude": profile["lat"],
        "longitude": profile["lon"],
        "daily": "temperature_2m_max,weather_code",
        "forecast_days": min(max(days, 1), 16),
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        return {"provider": "Open-Meteo", "mode": "error", "error": str(exc), "daily": []}

    temps = payload.get("daily", {}).get("temperature_2m_max", [])
    daily = [f"Mild, {round(temp)} C" for temp in temps]
    return {"provider": "Open-Meteo", "mode": "live", "city": profile["city"], "country": profile["country"], "daily": daily}
