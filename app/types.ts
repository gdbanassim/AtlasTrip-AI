export type AgentStatus = "queued" | "running" | "complete" | "warning";

export type AgentStep = {
  id: string;
  title: string;
  tool: string;
  detail: string;
  status: AgentStatus;
  durationMs: number;
};

export type DayPlan = {
  day: number;
  title: string;
  neighborhood: string;
  weather: string;
  total: number;
  blocks: {
    time: string;
    title: string;
    description: string;
    cost: number;
    transit: string;
  }[];
};

export type BookingOption = {
  type: "flight" | "hotel";
  name: string;
  provider: string;
  price: number;
  meta: string;
  action: string;
};

export type TripPlan = {
  destination: string;
  origin: string;
  days: number;
  budget: number;
  confidence: number;
  total: number;
  summary: string;
  budgetBreakdown: {
    label: string;
    value: number;
    tone: string;
  }[];
  daysPlan: DayPlan[];
  bookings: BookingOption[];
  agentSteps: AgentStep[];
  tools: {
    name: string;
    mode: "live" | "demo" | "not configured";
    note: string;
  }[];
};

export type PlannerRequest = {
  prompt: string;
  budget: number;
  days: number;
  origin: string;
  pace: "relaxed" | "balanced" | "packed";
  hotel: "budget" | "comfort" | "boutique";
  interests: string[];
};
