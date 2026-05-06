from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.mcp_tools.destination_resolver import is_airport_code, resolve_destination
from app.mcp_tools.tool_parsing import safe_int


async def search_booking_offers(
    settings: Settings,
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    adults: int = 1,
) -> dict[str, Any]:
    """Search Duffel test-mode offers for a safe booking demo."""
    if not settings.duffel_access_token:
        return {"provider": "Duffel Test Mode", "mode": "not configured", "offers": []}

    origin_profile = await resolve_destination(settings, origin) if not is_airport_code(origin) else {"airport": origin.upper()}
    destination_profile = await resolve_destination(settings, destination)
    body = {
        "data": {
            "slices": [
                {"origin": origin_profile["airport"], "destination": destination_profile["airport"], "departure_date": outbound_date},
                {"origin": destination_profile["airport"], "destination": origin_profile["airport"], "departure_date": return_date},
            ],
            "passengers": [{"type": "adult"} for _ in range(adults)],
            "cabin_class": "economy",
        }
    }
    headers = {
        "Authorization": f"Bearer {settings.duffel_access_token}",
        "Duffel-Version": "v2",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                "https://api.duffel.com/air/offer_requests",
                params={"return_offers": "true"},
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        return {"provider": "Duffel Test Mode", "mode": "error", "error": str(exc), "offers": []}

    offers = []
    for offer in payload.get("data", {}).get("offers", [])[:5]:
        offers.append(
            {
                "id": offer.get("id"),
                "price": safe_int(offer.get("total_amount")),
                "currency": offer.get("total_currency"),
                "expires_at": offer.get("expires_at"),
            }
        )

    return {"provider": "Duffel Test Mode", "mode": "live", "arrival_airport": destination_profile["airport"], "offers": offers}
