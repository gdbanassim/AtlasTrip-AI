from __future__ import annotations

import re
from typing import Any

import httpx

from app.config import Settings


FALLBACK_DESTINATIONS: dict[str, dict[str, Any]] = {
    "japan": {"airport": "NRT", "city": "Tokyo", "country": "JP", "lat": 35.6762, "lon": 139.6503},
    "tokyo": {"airport": "NRT", "city": "Tokyo", "country": "JP", "lat": 35.6762, "lon": 139.6503},
    "paris": {"airport": "CDG", "city": "Paris", "country": "FR", "lat": 48.8566, "lon": 2.3522},
    "london": {"airport": "LHR", "city": "London", "country": "GB", "lat": 51.5072, "lon": -0.1276},
    "dubai": {"airport": "DXB", "city": "Dubai", "country": "AE", "lat": 25.2048, "lon": 55.2708},
    "new york": {"airport": "JFK", "city": "New York", "country": "US", "lat": 40.7128, "lon": -74.0060},
}


async def resolve_destination(settings: Settings, destination: str) -> dict[str, Any]:
    """Resolve a free-form city/country into coordinates, country, city, and nearest airport."""
    clean_destination = destination.strip()
    if not settings.geoapify_api_key:
        return fallback_destination(clean_destination)

    geocoded = await geocode_destination(settings, clean_destination)
    if not geocoded:
        return fallback_destination(clean_destination)
    if geocoded.get("lat") is None or geocoded.get("lon") is None:
        return fallback_destination(clean_destination)

    airport = await nearest_airport_code(settings, geocoded["lat"], geocoded["lon"])
    geocoded["airport"] = airport or fallback_airport(clean_destination, geocoded)
    return geocoded


async def geocode_destination(settings: Settings, destination: str) -> dict[str, Any] | None:
    params = {
        "text": destination,
        "limit": 1,
        "format": "json",
        "apiKey": settings.geoapify_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://api.geoapify.com/v1/geocode/search", params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return None

    results = payload.get("results") or []
    if not results:
        return None

    result = results[0]
    country_code = result.get("country_code") or ""
    return {
        "airport": None,
        "city": best_city_name(result, destination),
        "country": country_code.upper() if country_code else "",
        "lat": result.get("lat"),
        "lon": result.get("lon"),
        "formatted": result.get("formatted") or destination,
    }


async def nearest_airport_code(settings: Settings, lat: float, lon: float) -> str | None:
    params = {
        "categories": "airport",
        "filter": f"circle:{lon},{lat},150000",
        "bias": f"proximity:{lon},{lat}",
        "limit": 10,
        "apiKey": settings.geoapify_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://api.geoapify.com/v2/places", params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return None

    for feature in payload.get("features", []):
        code = airport_code_from_feature(feature)
        if code:
            return code

    return None


def best_city_name(result: dict[str, Any], fallback: str) -> str:
    return (
        result.get("city")
        or result.get("town")
        or result.get("village")
        or result.get("municipality")
        or result.get("county")
        or result.get("state")
        or result.get("country")
        or fallback
    )


def airport_code_from_feature(feature: dict[str, Any]) -> str | None:
    properties = feature.get("properties") or {}
    raw = (properties.get("datasource") or {}).get("raw") or {}
    candidates = [
        properties.get("iata"),
        properties.get("iata_code"),
        raw.get("iata"),
        raw.get("iata_code"),
        raw.get("ref"),
        raw.get("icao"),
    ]

    for candidate in candidates:
        if isinstance(candidate, str):
            match = re.search(r"\b[A-Z]{3}\b", candidate.upper())
            if match:
                return match.group(0)

    return None


def fallback_destination(destination: str) -> dict[str, Any]:
    normalized = destination.strip().lower()
    for key, profile in FALLBACK_DESTINATIONS.items():
        if key in normalized:
            return profile.copy()

    airport = destination.upper() if is_airport_code(destination) else destination[:3].upper()
    return {"airport": airport, "city": destination, "country": "", "lat": 40.7128, "lon": -74.0060}


def fallback_airport(destination: str, resolved: dict[str, Any]) -> str:
    if is_airport_code(destination):
        return destination.upper()

    city = resolved.get("city") or destination
    return str(city)[:3].upper()


def is_airport_code(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{3}", value.strip()))
