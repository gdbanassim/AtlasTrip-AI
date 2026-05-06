import re

from app.config import Settings
from app.schemas import AgentStatus, AgentStep, BookingOption, BudgetItem, DayBlock, DayPlan, PlannerRequest, ToolInfo, TripPlan
from app.mcp_tools.attraction_search import find_attractions
from app.mcp_tools.flight_booking import search_booking_offers
from app.mcp_tools.flight_search import search_flights
from app.mcp_tools.hotel_search import search_hotels
from app.mcp_tools.destination_resolver import resolve_destination
from app.mcp_tools.tool_parsing import default_trip_dates, safe_int
from app.mcp_tools.weather_forecast import get_weather
from app.services.tool_registry import list_travel_tools


STEP_TEMPLATES = [
    ("parse", "Parsing trip constraints", "Groq + Pydantic", "Extracted destination, budget ceiling, origin, pace, and interest tags."),
    ("budget", "Building budget envelope", "Budget planner node", "Reserved money for flights, stay, transport, food, activities, and buffer."),
    ("flights", "Searching flight candidates", "SerpApi Google Flights", "Using live Google Flights search if SERPAPI_API_KEY exists, otherwise realistic demo pricing."),
    ("booking", "Checking booking sandbox", "Duffel Test Mode", "Preparing a safe flight booking demo flow without charging real money."),
    ("hotels", "Evaluating hotels", "LiteAPI Hotels", "Compared nightly cost, area fit, cancellation quality, and distance to routes."),
    ("weather", "Checking trip weather", "Open-Meteo", "Matched indoor and outdoor activities against expected daily conditions."),
    ("places", "Finding places and routes", "OpenTripMap + Geoapify", "Clustered attractions into efficient daily neighborhoods."),
    ("solve", "Solving constraints", "Itinerary optimizer", "Filtered options that exceed budget, overload days, or create long backtracking."),
    ("present", "Preparing booking handoff", "Booking advisor", "Created confirmation-safe booking options with provider handoff actions."),
]


async def build_trip_plan(request: PlannerRequest, settings: Settings) -> TripPlan:
    destination = infer_destination(request.prompt)
    resolved_destination = await resolve_destination(settings, destination)
    destination_meta = destination_profile(destination, resolved_destination)
    outbound_date, return_date = dates_from_prompt(request.prompt, request.days)
    weather_result = await get_weather(settings, destination, request.days)
    weather = weather_result.get("daily") or ["Weather unavailable"]
    flight_result = await search_flights(settings, request.origin, destination_meta["city"], outbound_date, return_date, request.budget)
    duffel_result = await search_booking_offers(settings, request.origin, destination_meta["city"], outbound_date, return_date)
    hotel_result = await search_hotels(settings, destination_meta["city"], outbound_date, return_date)
    attraction_result = await find_attractions(settings, destination_meta["city"], request.interests)

    flight_cost = first_available_price(flight_result.get("offers")) or min(round(request.budget * 0.38), 620)
    hotel_night = {"budget": 62, "comfort": 88, "boutique": 126}[request.hotel]
    hotel_cost = first_available_price(hotel_result.get("hotels")) or hotel_night * max(request.days - 1, 1)
    activity_cost = {"packed": request.days * 42, "balanced": request.days * 31, "relaxed": request.days * 24}[request.pace]
    food_cost = request.days * 38
    transit_cost = request.days * 18
    buffer = max(75, round(request.budget * 0.08))
    total = flight_cost + hotel_cost + activity_cost + food_cost + transit_cost + buffer

    days_plan = [
        build_day(
            day=index + 1,
            city=destination_meta["city"],
            neighborhood=destination_meta["neighborhoods"][index % len(destination_meta["neighborhoods"])],
            weather=weather[index % len(weather)],
            interest=request.interests[index % len(request.interests)],
            pace=request.pace,
            daily_total=round(activity_cost / request.days + food_cost / request.days + transit_cost / request.days),
        )
        for index in range(request.days)
    ]

    flight_search_live = flight_result.get("mode") == "live"
    flight_booking_demo = duffel_result.get("mode") == "live"
    hotel_search_live = hotel_result.get("mode") == "live"
    tools = [ToolInfo(name=tool.name, mode=tool.mode, note=tool.note) for tool in list_travel_tools(settings)]

    return TripPlan(
        destination=destination_meta["city"],
        origin=request.origin.upper(),
        days=request.days,
        budget=request.budget,
        confidence=91 if total <= request.budget else 76,
        total=total,
        summary=(
            f"This plan fits under ${request.budget:,} with a protected buffer and booking choices that avoid risky automatic purchases."
            if total <= request.budget
            else f"The best current plan is above budget by ${total - request.budget:,}; reduce hotel comfort, pace, or origin/date constraints to bring it down."
        ),
        budgetBreakdown=[
            BudgetItem(label="Flights", value=flight_cost, tone="ink"),
            BudgetItem(label="Hotels", value=hotel_cost, tone="moss"),
            BudgetItem(label="Food", value=food_cost, tone="brass"),
            BudgetItem(label="Activities", value=activity_cost, tone="blue"),
            BudgetItem(label="Transit", value=transit_cost, tone="slate"),
            BudgetItem(label="Buffer", value=buffer, tone="stone"),
        ],
        daysPlan=days_plan,
        bookings=[
            BookingOption(
                type="flight",
                name=f"{request.origin.upper()} to {destination_meta['city']}",
                provider=flight_result.get("provider", "SerpApi Google Flights"),
                price=flight_cost,
                meta=(
                    flight_meta(flight_result)
                    if flight_search_live
                    else "Provider unavailable; using planner estimate"
                ),
                action="Review flight options",
            ),
            BookingOption(
                type="hotel",
                name=hotel_name(hotel_result, request.hotel),
                provider=hotel_result.get("provider", "LiteAPI Hotels"),
                price=hotel_cost,
                meta=(
                    f"{max(request.days - 1, 1)} nights, live hotel rate"
                    if hotel_search_live
                    else f"{max(request.days - 1, 1)} nights, provider unavailable; using planner estimate"
                ),
                action="Compare hotel rooms",
            ),
        ],
        agentSteps=[
            AgentStep(
                id=step_id,
                title=title,
                tool=tool,
                detail=detail,
                status=tool_status(
                    step_id,
                    flight_search_live,
                    flight_booking_demo,
                    hotel_search_live,
                    weather_result.get("mode") == "live",
                    attraction_result.get("mode") == "live",
                ),
                durationMs=420 + index * 180,
            )
            for index, (step_id, title, tool, detail) in enumerate(STEP_TEMPLATES)
        ],
        tools=tools,
    )


def tool_status(
    step_id: str,
    flight_search_live: bool,
    flight_booking_demo: bool,
    hotel_search_live: bool,
    weather_live: bool,
    attractions_live: bool,
) -> AgentStatus:
    if step_id == "flights" and not flight_search_live:
        return "warning"
    if step_id == "booking" and not flight_booking_demo:
        return "warning"
    if step_id == "hotels" and not hotel_search_live:
        return "warning"
    if step_id == "weather" and not weather_live:
        return "warning"
    if step_id == "places" and not attractions_live:
        return "warning"
    return "complete"


def dates_from_prompt(prompt: str, days: int) -> tuple[str, str]:
    dates = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", prompt)
    if len(dates) >= 2:
        return dates[0], dates[1]
    return default_trip_dates(days)


def first_available_price(items: object) -> int | None:
    if not isinstance(items, list):
        return None

    prices = []
    for item in items:
        if isinstance(item, dict):
            price = safe_int(item.get("price"))
            if price:
                prices.append(price)
    return min(prices) if prices else None


def flight_meta(result: dict) -> str:
    offers = result.get("offers")
    if not isinstance(offers, list) or not offers:
        return "Live search returned no available fares"

    offer = offers[0]
    airline = offer.get("airline") or "airline option"
    stops = offer.get("stops")
    stop_text = "direct" if stops == 0 else f"{stops} stop" if stops == 1 else f"{stops} stops"
    return f"{airline}, {stop_text}, live fare search"


def hotel_name(result: dict, hotel_tier: str) -> str:
    hotels = result.get("hotels")
    if isinstance(hotels, list) and hotels and isinstance(hotels[0], dict):
        name = hotels[0].get("name")
        if name:
            return str(name)
    return {"budget": "Clean budget stay", "comfort": "Transit-friendly comfort hotel", "boutique": "Small design hotel"}[hotel_tier]


def build_day(day: int, city: str, neighborhood: str, weather: str, interest: str, pace: str, daily_total: int) -> DayPlan:
    return DayPlan(
        day=day,
        title=day_title(city, day, interest),
        neighborhood=neighborhood,
        weather=weather,
        total=daily_total,
        blocks=[
            DayBlock(
                time="09:00",
                title=f"{neighborhood} orientation walk",
                description=f"Start with a low-cost neighborhood route tuned for {interest.lower()} and easy transit access.",
                cost=8,
                transit="Metro plus walking, 22 min",
            ),
            DayBlock(
                time="13:00",
                title="Local lunch and anchor attraction",
                description="Pick one paid highlight, then keep nearby stops free so the daily budget stays controlled.",
                cost=32 if pace == "packed" else 24,
                transit="Short transfer, 14 min",
            ),
            DayBlock(
                time="18:00",
                title="Evening food street",
                description="A flexible dinner block with a cheaper fallback and one premium option if the budget is still green.",
                cost=28,
                transit="Walkable cluster",
            ),
        ],
    )


def infer_destination(prompt: str) -> str:
    patterns = [
        r"\bfrom\s+[A-Z][A-Za-z .'-]+?\s+to\s+([A-Z][A-Za-z .'-]+?)(?=\s+(?:trip|itinerary|route|travel plan|vacation|holiday)\b|[,.]|$)",
        r"\b(?:to|in|for)\s+([A-Z][A-Za-z .'-]+?)(?=\s+(?:trip|itinerary|route|travel plan|vacation|holiday)\b|[,.]|$)",
        r"\b(?:Create|Build|Plan|Make|Generate)\s+(?:a|an|the)?\s*(?:(?:short|quick|practical|budget|budget-friendly|affordable|relaxed|balanced|packed|simple|detailed|premium|luxury|local)\s+)*([A-Z][A-Za-z .'-]+?)\s+(?:trip|itinerary|route|travel plan|vacation|holiday)\b",
        r"\b([A-Z][A-Za-z .'-]+?)\s+(?:trip|itinerary|route|travel plan|vacation|holiday)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt)
        if match:
            destination = clean_destination(match.group(1))
            if destination:
                return destination

    capitalized = re.findall(r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2}\b", prompt)
    for candidate in capitalized:
        destination = clean_destination(candidate)
        if destination and destination.lower() not in {"create", "build", "plan", "make", "generate"}:
            return destination

    return prompt.strip()


def clean_destination(destination: str) -> str:
    destination = re.sub(r"\b(?:focused|with|under|from|for|including|include|and|or)\b.*$", "", destination, flags=re.IGNORECASE)
    destination = re.sub(
        r"^(?:a|an|the|short|quick|practical|budget|budget-friendly|affordable|relaxed|balanced|packed|simple|detailed|premium|luxury|local)\s+",
        "",
        destination.strip(),
        flags=re.IGNORECASE,
    )
    return destination.strip(" .,")


def destination_profile(destination: str, resolved: dict[str, object]) -> dict[str, object]:
    city = str(resolved.get("city") or destination)
    return {
        "city": city,
        "neighborhoods": [f"{city} center", "Historic quarter", "Market district", "Museum area", "Transit hub"],
    }


def day_title(destination: str, day: int, interest: str) -> str:
    return f"{destination} {interest.lower()} route and local highlights"
