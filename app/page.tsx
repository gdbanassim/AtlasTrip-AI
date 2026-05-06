"use client";

import { useMemo, useState } from "react";
import {
  ArrowRight,
  BadgeDollarSign,
  CalendarDays,
  CheckCircle2,
  CircleDot,
  Clock3,
  Compass,
  Hotel,
  Loader2,
  Map,
  Plane,
  Route,
  Settings2,
  ShieldCheck,
  Sparkles,
  SunMedium,
  WalletCards
} from "lucide-react";
import type { AgentStep, PlannerRequest, TripPlan } from "@/app/types";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const interests = ["Food", "Culture", "Museums", "Nature", "Shopping", "Nightlife", "Anime", "Temples"];

const simulatedSteps: AgentStep[] = [
  { id: "parse", title: "Parsing trip constraints", tool: "Groq + Zod", detail: "Reading natural language request.", status: "queued", durationMs: 0 },
  { id: "budget", title: "Building budget envelope", tool: "LangGraph", detail: "Splitting spend by category.", status: "queued", durationMs: 0 },
  { id: "flights", title: "Searching flight candidates", tool: "SerpApi", detail: "Checking Google Flights-style fare bands.", status: "queued", durationMs: 0 },
  { id: "booking", title: "Checking booking sandbox", tool: "Duffel", detail: "Preparing safe demo booking actions.", status: "queued", durationMs: 0 },
  { id: "hotels", title: "Evaluating hotels", tool: "LiteAPI", detail: "Comparing nightly rates and areas.", status: "queued", durationMs: 0 },
  { id: "weather", title: "Checking weather", tool: "Open-Meteo", detail: "Pairing activity choices with forecast.", status: "queued", durationMs: 0 },
  { id: "places", title: "Finding places and routes", tool: "OpenTripMap", detail: "Clustering nearby stops.", status: "queued", durationMs: 0 },
  { id: "solve", title: "Solving constraints", tool: "Optimizer", detail: "Minimizing backtracking and overruns.", status: "queued", durationMs: 0 },
  { id: "present", title: "Preparing booking handoff", tool: "Advisor", detail: "Creating confirmation-safe actions.", status: "queued", durationMs: 0 }
];

export default function Home() {
  const [request, setRequest] = useState<PlannerRequest>({
    prompt: "",
    budget: 1500,
    days: 5,
    origin: "",
    pace: "balanced",
    hotel: "budget",
    interests: ["Food", "Culture", "Temples", "Anime"]
  });
  const [plan, setPlan] = useState<TripPlan | null>(null);
  const [steps, setSteps] = useState<AgentStep[]>(simulatedSteps);
  const [activeDay, setActiveDay] = useState(1);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const remaining = useMemo(() => {
    if (!plan) return null;
    return plan.budget - plan.total;
  }, [plan]);

  async function runPlanner() {
    if (request.prompt.trim().length < 5) {
      setError("Enter a trip request first.");
      return;
    }

    if (request.origin.trim().length < 2) {
      setError("Enter an origin airport or city.");
      return;
    }

    setIsRunning(true);
    setError(null);
    setPlan(null);
    setActiveDay(1);
    setSteps(simulatedSteps.map((step) => ({ ...step, status: "queued", durationMs: 0 })));

    simulatedSteps.forEach((_, index) => {
      window.setTimeout(() => {
        setSteps((current) =>
          current.map((step, stepIndex) => {
            if (stepIndex < index) return { ...step, status: "complete", durationMs: 520 + stepIndex * 160 };
            if (stepIndex === index) return { ...step, status: "running" };
            return step;
          })
        );
      }, index * 360);
    });

    try {
      const response = await fetch(`${apiBaseUrl}/api/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error("FastAPI planner returned an invalid response.");
      }

      const data = (await response.json()) as TripPlan;
      window.setTimeout(() => {
        setPlan(data);
        setSteps(data.agentSteps);
        setIsRunning(false);
      }, 3100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Planner failed.");
      setIsRunning(false);
    }
  }

  function toggleInterest(interest: string) {
    setRequest((current) => {
      const hasInterest = current.interests.includes(interest);
      const nextInterests = hasInterest
        ? current.interests.filter((item) => item !== interest)
        : [...current.interests, interest];

      return { ...current, interests: nextInterests.length ? nextInterests : [interest] };
    });
  }

  const selectedDay = plan?.daysPlan.find((day) => day.day === activeDay) ?? plan?.daysPlan[0];

  return (
    <main className="shell">
      <section className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <Compass size={22} />
          </div>
          <div>
            <p>AtlasTrip AI</p>
            <span>Autonomous travel planner with real-tool handoff</span>
          </div>
        </div>
        <div className="status-strip">
          <span><ShieldCheck size={16} /> Human-confirmed bookings</span>
          <span><CircleDot size={16} /> Groq-ready agent graph</span>
        </div>
      </section>

      <section className="hero-grid">
        <div className="planner-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Trip Command</span>
              <h1>Build a budget-smart itinerary that can be edited live.</h1>
            </div>
            <Settings2 size={22} />
          </div>

          <label className="field wide">
            <span>Request</span>
            <textarea
              value={request.prompt}
              placeholder="Plan a 5-day Japan trip under $1500 from LAX. I want food, culture, temples, and one anime stop."
              onChange={(event) => setRequest({ ...request, prompt: event.target.value })}
              rows={5}
            />
          </label>

          <div className="control-grid">
            <label className="field">
              <span>Budget</span>
              <input
                type="number"
                value={request.budget}
                onChange={(event) => setRequest({ ...request, budget: Number(event.target.value) })}
              />
            </label>
            <label className="field">
              <span>Days</span>
              <input
                type="number"
                value={request.days}
                min={1}
                max={30}
                onChange={(event) => setRequest({ ...request, days: Number(event.target.value) })}
              />
            </label>
            <label className="field">
              <span>Origin</span>
              <input
                value={request.origin}
                placeholder="LAX"
                onChange={(event) => setRequest({ ...request, origin: event.target.value.toUpperCase() })}
              />
            </label>
          </div>

          <div className="option-group">
            <span>Pace</span>
            <div className="segmented" aria-label="Pace">
              {(["relaxed", "balanced", "packed"] as const).map((pace) => (
                <button
                  key={pace}
                  className={request.pace === pace ? "active" : ""}
                  onClick={() => setRequest({ ...request, pace })}
                >
                  {pace}
                </button>
              ))}
            </div>
          </div>

          <div className="option-group">
            <span>Hotel Style</span>
            <div className="segmented" aria-label="Hotel style">
              {(["budget", "comfort", "boutique"] as const).map((hotel) => (
                <button
                  key={hotel}
                  className={request.hotel === hotel ? "active" : ""}
                  onClick={() => setRequest({ ...request, hotel })}
                >
                  {hotel}
                </button>
              ))}
            </div>
          </div>

          <div className="option-group">
            <span>Interests</span>
            <div className="interest-grid" aria-label="Interests">
              {interests.map((interest) => (
                <button
                  key={interest}
                  className={request.interests.includes(interest) ? "active" : ""}
                  onClick={() => toggleInterest(interest)}
                >
                  {interest}
                </button>
              ))}
            </div>
          </div>

          <button className="primary-action" onClick={runPlanner} disabled={isRunning}>
            {isRunning ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />}
            {isRunning ? "Planning trip" : "Run autonomous planner"}
            <ArrowRight size={18} />
          </button>

          {error ? <p className="error">{error}</p> : null}
        </div>

        <div className="map-panel">
          <div className="map-top">
            <div>
              <span className="eyebrow">Live Preview</span>
              <h2>{plan ? `${plan.destination} from ${plan.origin}` : "Planning canvas"}</h2>
            </div>
            <Map size={21} />
          </div>
          <div className="map-canvas">
            {plan ? (
              <>
                <div className="route-line" />
                {plan.daysPlan.slice(0, 4).map((day, index) => (
                  <div className={`pin pin-${["a", "b", "c", "d"][index]}`} key={day.day}>
                    {day.day}
                  </div>
                ))}
                {plan.daysPlan.slice(0, 3).map((day, index) => (
                  <div className={`district district-${["a", "b", "c"][index]}`} key={day.neighborhood}>
                    {day.neighborhood}
                  </div>
                ))}
              </>
            ) : (
              <div className="map-empty">
                <Map size={28} />
                <p>Route preview appears after the backend returns a plan.</p>
              </div>
            )}
          </div>
          <div className="metric-row">
            <Metric icon={<WalletCards size={18} />} label="Estimated total" value={plan ? `$${plan.total.toLocaleString()}` : "Not planned"} />
            <Metric
              icon={<BadgeDollarSign size={18} />}
              label="Budget room"
              value={remaining === null ? "Not planned" : `${remaining >= 0 ? "+" : "-"}$${Math.abs(remaining).toLocaleString()}`}
            />
            <Metric icon={<Clock3 size={18} />} label="Trip length" value={`${request.days} days`} />
          </div>
        </div>

        <AgentPanel steps={steps} tools={plan?.tools} isRunning={isRunning} />
      </section>

      <section className="content-grid">
        <div className="itinerary-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Timeline</span>
              <h2>{plan ? plan.summary : "Run the planner to generate a route-optimized itinerary."}</h2>
            </div>
            <CalendarDays size={22} />
          </div>

          {plan ? (
            <div className="day-tabs">
              {plan.daysPlan.map((day) => (
                <button
                  key={day.day}
                  className={activeDay === day.day ? "active" : ""}
                  onClick={() => setActiveDay(day.day)}
                >
                  Day {day.day}
                </button>
              ))}
            </div>
          ) : null}

          {selectedDay ? (
            <article className="day-card">
              <div className="day-card-head">
                <div>
                  <span>{selectedDay.neighborhood}</span>
                  <h3>{selectedDay.title}</h3>
                </div>
                <p><SunMedium size={16} /> {selectedDay.weather}</p>
              </div>
              <div className="timeline">
                {selectedDay.blocks.map((block) => (
                  <div className="timeline-item" key={`${selectedDay.day}-${block.time}`}>
                    <time>{block.time}</time>
                    <div>
                      <h4>{block.title}</h4>
                      <p>{block.description}</p>
                      <span><Route size={14} /> {block.transit} - ${block.cost}</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          ) : (
            <div className="empty-state">
              <Plane size={28} />
              <p>Your day-by-day plan will appear here after the agent finishes.</p>
            </div>
          )}
        </div>

        <aside className="finance-panel">
          <div className="section-heading compact">
            <div>
              <span className="eyebrow">Cost Control</span>
              <h2>Budget breakdown</h2>
            </div>
            <WalletCards size={21} />
          </div>

          {plan ? (
            <>
              <div className="budget-list">
                {plan.budgetBreakdown.map((item) => (
                  <div className="budget-item" key={item.label}>
                    <div>
                      <span className={`dot ${item.tone}`} />
                      <p>{item.label}</p>
                    </div>
                    <strong>${item.value.toLocaleString()}</strong>
                  </div>
                ))}
              </div>

              <div className={remaining !== null && remaining >= 0 ? "budget-total positive" : "budget-total negative"}>
                <span>{remaining !== null && remaining >= 0 ? "Remaining buffer" : "Over budget"}</span>
                <strong>${Math.abs(remaining ?? 0).toLocaleString()}</strong>
              </div>
            </>
          ) : (
            <div className="empty-state compact-empty">
              <WalletCards size={24} />
              <p>Budget categories will appear after planning.</p>
            </div>
          )}

          <div className="booking-list">
            <h3>Booking suggestions</h3>
            {plan?.bookings.map((booking) => (
              <div className="booking-card" key={booking.name}>
                <div className="booking-icon">
                  {booking.type === "flight" ? <Plane size={18} /> : <Hotel size={18} />}
                </div>
                <div>
                  <strong>{booking.name}</strong>
                  <p>{booking.provider} - {booking.meta}</p>
                  <button>{booking.action}</button>
                </div>
                <span>${booking.price.toLocaleString()}</span>
              </div>
            ))}
            {!plan ? <p className="muted">Booking options appear after planning. Real purchases always require confirmation.</p> : null}
          </div>
        </aside>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="metric">
      {icon}
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function AgentPanel({
  steps,
  tools,
  isRunning
}: {
  steps: AgentStep[];
  tools?: TripPlan["tools"];
  isRunning: boolean;
}) {
  return (
    <aside className="agent-panel">
      <div className="panel-heading compact">
        <div>
          <span className="eyebrow">Agent Runtime</span>
          <h2>{isRunning ? "Graph is executing" : "Tool graph ready"}</h2>
        </div>
        <Loader2 className={isRunning ? "spin" : ""} size={21} />
      </div>

      <div className="agent-steps">
        {steps.map((step) => (
          <div className={`agent-step ${step.status}`} key={step.id}>
            <div className="step-status">
              {step.status === "complete" || step.status === "warning" ? <CheckCircle2 size={17} /> : <CircleDot size={17} />}
            </div>
            <div>
              <strong>{step.title}</strong>
              <p>{step.detail}</p>
              <span>{step.tool}{step.durationMs ? ` - ${step.durationMs} ms` : ""}</span>
            </div>
          </div>
        ))}
      </div>

      {tools ? (
        <div className="tool-grid">
          {tools.map((tool) => (
            <div className="tool-pill" key={tool.name}>
              <span className={tool.mode === "live" ? "live" : tool.mode === "demo" ? "demo" : ""}>{tool.mode}</span>
              <strong>{tool.name}</strong>
              <p>{tool.note}</p>
            </div>
          ))}
        </div>
      ) : null}
    </aside>
  );
}
