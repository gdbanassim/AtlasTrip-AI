# AtlasTrip AI

Autonomous travel planner demo with a FastAPI Python backend and a Next.js frontend.

## Structure

- `backend/` - FastAPI API service for planning, budget logic, tool status, weather lookup, and booking suggestions.
- `backend/app/mcp_tools/` - flat MCP tool modules, one purpose per file.
- `backend/app/services/` - planner orchestration and tool registry/status metadata.
- `app/` - Next.js frontend with the modern planner UI, live agent timeline, itinerary, budget, and booking cards.

MCP tool modules:

- `flight_search.py` - Google Flights price search through SerpApi.
- `flight_booking.py` - Duffel test-mode flight booking sandbox.
- `hotel_search.py` - LiteAPI hotel rates.
- `weather_forecast.py` - Open-Meteo forecast data.
- `attraction_search.py` - OpenTripMap attraction discovery.
- `destination_resolver.py` - Geoapify-powered city/country resolver with nearest-airport lookup.
- `tool_parsing.py` - date and price parsing helpers.

## Run Backend

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

If `python` is not recognized, install Python 3.12+ and reopen the terminal.

Backend endpoints:

- `GET http://localhost:8000/health`
- `POST http://localhost:8000/api/plan`

## Run MCP Travel Tools

The travel integrations are also exposed as an MCP server. FastAPI is still used for the browser UI, while MCP is the agent/tool layer for SerpApi, Duffel, LiteAPI, Open-Meteo, and OpenTripMap.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.mcp_tools.server
```

MCP tools exposed:

- `search_flight_prices`
- `search_booking_sandbox`
- `search_hotel_rates`
- `get_destination_weather`
- `find_destination_attractions`

## Run Frontend

Open another terminal from the project root:

```powershell
npm.cmd install
copy .env.example .env.local
npm.cmd run dev
```

Then visit:

```text
http://localhost:3000
```

## API Keys

The root `.env` is for the Next.js frontend and should only contain public variables:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The backend `backend/.env` is where private API keys belong:

```env
FRONTEND_ORIGIN=http://localhost:3000
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
SERPAPI_API_KEY=
DUFFEL_ACCESS_TOKEN=
LITEAPI_KEY=
GEOAPIFY_API_KEY=
OPENTRIPMAP_API_KEY=
```

Never put private keys in a variable starting with `NEXT_PUBLIC_`, because those are exposed to the browser.

The MVP uses real search/tool adapters where free APIs are available, but real purchases should always stay behind explicit user confirmation.
