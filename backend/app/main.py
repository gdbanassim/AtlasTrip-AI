from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.schemas import PlannerRequest, TripPlan
from app.services.planner import build_trip_plan

settings = get_settings()

app = FastAPI(
    title="AtlasTrip API",
    version="0.1.0",
    description="FastAPI backend for autonomous travel planning with free/freemium tool adapters.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "atlastrip-backend"}


@app.post("/api/plan", response_model=TripPlan)
async def plan_trip(payload: PlannerRequest, settings: Settings = Depends(get_settings)) -> TripPlan:
    return await build_trip_plan(payload, settings)
