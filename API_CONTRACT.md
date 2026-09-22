# MealTracker API Contract (v2)

Single source of truth shared by the backend (FastAPI + agent) and the frontend
(vanilla JS). If a change is needed on either side, update this file first.

Base URL: same origin (`/api/...`). All bodies are JSON.

## Types

### State
Unchanged shape from `memory_store.summary()`:

```json
{
  "budget": 2000,          // number | null
  "consumed": 500,         // number
  "remaining": 1500,       // number | null (null when budget unset)
  "meal_count": 2,
  "meals": [ { "food": "Apple", "calories": 95, "estimated": false, "source": "local" } ]
}
```

### TraceStep
Emitted one at a time while the agent works. `step` is one of:
`read_memory_context`, `agent_iteration`, `tool_call`, `tool_result`,
`tool_arguments_error`, `scope_check`, `llm_error`, `final_answer`.

```json
{
  "id": "s4",                 // unique within the run: "s1", "s2", ...
  "step": "tool_call",
  "tool": "lookup_calories",  // optional
  "arguments": { "food": "apple" },  // optional
  "result": { ... },          // optional, any JSON value
  "iteration": 2,             // optional, 1-based
  "ts": 812.5,                // ms since run start
  "duration_ms": 210.4        // optional: on agent_iteration = LLM latency;
                              // on tool_result = tool execution time
}
```

### Card
Structured, deterministic UI cards computed from tool calls and memory diffs —
never parsed from model prose. `type` is one of:

```json
{ "type": "breakdown",
  "title": "Apple + yogurt",
  "items": [ { "food": "Apple", "calories": 95, "estimated": false } ],
  "total": 180,
  "remaining_before": 1500,    // null when no budget
  "remaining_after": 1320,     // null when no budget
  "verdict": "fits" }          // "fits" | "over" | "unknown" (unknown = no budget)

{ "type": "meal_logged",  "food": "Aloo paratha", "calories": 300, "estimated": true,
  "consumed": 800, "remaining": 1200 }

{ "type": "meals_logged", "items": [ { "food": "Rice", "calories": 205, "estimated": false } ],
  "consumed": 705, "remaining": 1295 }

{ "type": "budget_set", "budget": 2000, "consumed": 500, "remaining": 1500 }

{ "type": "meal_removed", "food": "Banana", "calories": 105, "consumed": 395, "remaining": 1605 }

{ "type": "status", "budget": 2000, "consumed": 500, "remaining": 1500 }
```

Card rules (backend computes, order matters):
1. One or more **successful** `add_meal` calls → `meal_logged` (single) or
   `meals_logged` (2+). Numbers from state *after* the run.
2. Successful `set_calorie_budget` → `budget_set`.
3. Successful `remove_meal` → `meal_removed`.
4. `lookup_calories` calls with **no** `add_meal` in the same run → `breakdown`
   (title = the looked-up foods joined with " + "). `verdict` compares the
   lookup total against `remaining` at run start: `total <= remaining` →
   `fits`, else `over`; no budget → `unknown`.
5. `status` card only when state changed but no other card applies.
6. Round calories to clean ints when they are near-integers. Empty cards array
   `[]` is valid (pure conversation).

## Endpoints

### GET /api/state?session_id=…
→ `State`

### POST /api/chat
Body `{ "message": string, "session_id": string }`
→ `{ "reply": string, "trace": TraceStep[], "cards": Card[], "state": State, "session_id": string }`

Session rule: an empty/missing `session_id` resolves to `"default"` — never
mint a fresh UUID per request (that broke state persistence).

### POST /api/chat/stream  (NEW — Server-Sent Events)
Same body as `/api/chat`. Response `text/event-stream`, `Cache-Control: no-cache`.
Events, in order:

```
event: trace
data: <TraceStep JSON>

event: trace
data: <TraceStep JSON>

event: done
data: { "reply": string, "trace": TraceStep[], "cards": Card[], "state": State, "session_id": string }

```

On failure before completion:

```
event: error
data: { "message": string }
```

The stream closes after `done`/`error`. Each `data:` line is a single-line JSON
payload (no embedded raw newlines). `trace` events fire the moment each step
happens (e.g. `tool_call` before the tool executes). The `done` payload repeats
the full trace so a non-streaming consumer can render retroactively.

### POST /api/reset (NEW)
Body `{ "session_id": string }` → `{ "state": State }`
Clears budget + meals for the session server-side.

### POST /api/meals (NEW — direct log, no LLM)
Body `{ "session_id": string, "food": string, "calories": number?, "estimated": bool? }`
→ `{ "state": State }`
When `calories` is omitted the server resolves it via the local database /
estimation (same path `add_meal` tool uses) and sets `estimated` accordingly.

### DELETE /api/meals?session_id=…&food=… (NEW)
Removes the first case-insensitive match.
→ `{ "removed": bool, "state": State }`

### POST /api/budget
Unchanged: `{ "budget": float, "session_id": string }` → same shape as `/api/chat`.

### GET /api/health
Unchanged.

## Agent behavior changes

- `agent.run(...)` keeps its current return shape (plus `"cards"`) — `main.py`
  and non-streaming callers must keep working.
- New `agent.run_stream(...)` generator yields `("trace", TraceStep)` per step
  as it happens, and finally `("done", result_dict)`.
- **Single memory snapshot:** memory is injected into `messages` as ONE system
  message; when refreshed after tool rounds its content is replaced in place —
  no stacking of stale `UPDATED CURRENT MEMORY` snapshots.
- **Prompt:** the FINAL ANSWERS section forbids markdown/ASCII pipe tables
  (bullet lists instead), asks for short answers, and requires all numbers to
  come from the latest CURRENT MEMORY block only.
- `MAX_AGENT_STEPS` is a module-level constant (default 8), overridable via env
  `MAX_AGENT_STEPS` in `app/config.py`; honored by both `run` and `run_stream`.
- Trace is never truncated server-side; the client decides display limits.
- Client disconnect on `/api/chat/stream` should abort the run between steps
  where practical (no wasted LLM calls after the reader is gone).
