from typing import Literal

from pydantic import BaseModel, Field


AgentStatus = Literal["queued", "running", "complete", "warning"]
Pace = Literal["relaxed", "balanced", "packed"]
HotelTier = Literal["budget", "comfort", "boutique"]
ToolMode = Literal["live", "demo", "not configured"]


class PlannerRequest(BaseModel):
    prompt: str = Field(min_length=5)
    budget: int = Field(ge=300, le=50_000)
    days: int = Field(ge=1, le=30)
    origin: str = Field(min_length=2, max_length=8)
    pace: Pace
    hotel: HotelTier
    interests: list[str] = Field(min_length=1)


class AgentStep(BaseModel):
    id: str
    title: str
    tool: str
    detail: str
    status: AgentStatus
    durationMs: int


class DayBlock(BaseModel):
    time: str
    title: str
    description: str
    cost: int
    transit: str


class DayPlan(BaseModel):
    day: int
    title: str
    neighborhood: str
    weather: str
    total: int
    blocks: list[DayBlock]


class BookingOption(BaseModel):
    type: Literal["flight", "hotel"]
    name: str
    provider: str
    price: int
    meta: str
    action: str


class BudgetItem(BaseModel):
    label: str
    value: int
    tone: str


class ToolInfo(BaseModel):
    name: str
    mode: ToolMode
    note: str


class TripPlan(BaseModel):
    destination: str
    origin: str
    days: int
    budget: int
    confidence: int
    total: int
    summary: str
    budgetBreakdown: list[BudgetItem]
    daysPlan: list[DayPlan]
    bookings: list[BookingOption]
    agentSteps: list[AgentStep]
    tools: list[ToolInfo]
