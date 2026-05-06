from mcp.server.fastmcp import FastMCP

from app.config import get_settings
from app.mcp_tools.attraction_search import find_attractions
from app.mcp_tools.flight_booking import search_booking_offers
from app.mcp_tools.flight_search import search_flights
from app.mcp_tools.hotel_search import search_hotels
from app.mcp_tools.weather_forecast import get_weather

mcp = FastMCP("AtlasTrip Travel Tools", json_response=True)


@mcp.tool()
async def search_flight_prices(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    max_price: int | None = None,
) -> dict:
    """Search flight prices with SerpApi Google Flights."""
    return await search_flights(get_settings(), origin, destination, outbound_date, return_date, max_price)


@mcp.tool()
async def search_booking_sandbox(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    adults: int = 1,
) -> dict:
    """Search Duffel test-mode flight offers for safe booking demos."""
    return await search_booking_offers(get_settings(), origin, destination, outbound_date, return_date, adults)


@mcp.tool()
async def search_hotel_rates(
    destination: str,
    checkin: str,
    checkout: str,
    adults: int = 1,
) -> dict:
    """Search hotel rates with LiteAPI."""
    return await search_hotels(get_settings(), destination, checkin, checkout, adults)


@mcp.tool()
async def get_destination_weather(destination: str, days: int = 5) -> dict:
    """Get destination weather with Open-Meteo."""
    return await get_weather(get_settings(), destination, days)


@mcp.tool()
async def find_destination_attractions(destination: str, interests: list[str]) -> dict:
    """Find attractions with OpenTripMap."""
    return await find_attractions(get_settings(), destination, interests)


if __name__ == "__main__":
    mcp.run()
