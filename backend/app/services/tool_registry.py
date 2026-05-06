from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class ToolStatus:
    name: str
    mode: str
    note: str


def configured(value: str | None) -> str:
    return "live" if value else "not configured"


def list_travel_tools(settings: Settings) -> list[ToolStatus]:
    return [
        ToolStatus(
            "Groq LLM",
            configured(settings.groq_api_key),
            "Ready for live reasoning." if settings.groq_api_key else "Demo planner is active until GROQ_API_KEY is set.",
        ),
        ToolStatus(
            "SerpApi Google Flights",
            configured(settings.serpapi_api_key),
            "Flight price search with a small free monthly search allowance.",
        ),
        ToolStatus(
            "Duffel Test Mode",
            configured(settings.duffel_access_token),
            "Safe flight booking sandbox for demo orders without spending money.",
        ),
        ToolStatus(
            "LiteAPI Hotels",
            configured(settings.liteapi_key),
            "Hotel search and booking-style data for the accommodation flow.",
        ),
        ToolStatus("Open-Meteo", "live", "Free weather API without a key for non-commercial usage."),
        ToolStatus("Geoapify", configured(settings.geoapify_api_key), "Optional routing and geocoding free tier."),
        ToolStatus("OpenTripMap", configured(settings.opentripmap_api_key), "Optional attraction discovery free plan."),
    ]
