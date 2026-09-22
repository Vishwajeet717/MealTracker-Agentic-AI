# Meal Calorie Helper (T17) — CSE476 CA1

## Required explanation

**Purpose and tools.** This project tracks a user's meals against a daily
calorie budget (informational only) using a real Groq-backed agent, not a
scripted chatbot. The two official tools are `lookup_calories(food)`,
which checks a local reference table for a food's approximate calories,
and `add_meal(food)`, which logs a food (with its calories and where that
figure came from) into the current session's memory. Both are real Python
functions the LLM calls via Groq's tool-calling API — the model decides
when and whether to call them; the application layer only executes what
the model asks for.

**Memory and the plan-act loop.** Memory (`app/memory.py`) holds the
day's calorie budget, every meal logged, and the running consumed/
remaining totals, keyed by session ID so each user/tab has isolated
state. Every agent turn (`app/agent.py: run_agent()`) starts by reading
this memory back into the conversation, then runs a genuine multi-step
loop: the LLM receives the conversation, decides to call a tool or
answer, the tool executes and its result is appended to the conversation,
and the LLM sees that result before deciding its *next* action — repeated
until it produces a final answer. This is how "I had oatmeal and a
banana" turns into two `lookup_calories` calls followed by two `add_meal`
calls, and how a later question like "how many calories have I used
today?" is answered directly from memory instead of guessing.

**An honest failure and how it was handled.** Early in development,
`lookup_calories` treated any food missing from its local table as a hard
failure — an unknown dish like "dragon fruit cheesecake" caused the agent
to refuse to log it at all, which is unhelpful for a food-tracking tool
covering more than a tiny fixed dictionary of dishes. The fix keeps
`lookup_calories` honest (it still reports `found: false` for unknown
foods) but no longer treats that as a dead end: it returns explicit
`guidance` telling the LLM to produce its own reasonable estimate from
general nutrition knowledge and to clearly label it as approximate, and
`add_meal` accepts that estimate with `source="llm_estimate"` so the
distinction between a database value and an estimate is preserved all the
way to the UI (estimated calories are marked "· est." in the meal list).
The failure mode and its resolution are still visible in
`tests/test_tools.py::test_lookup_unknown_food_does_not_fail_hard`.

---

## Tools — official vs. extension

| Tool | Status | Purpose |
|---|---|---|
| `lookup_calories(food)` | **Official (required)** | Look up approximate calories for a food in a local reference table; reports `found=False` + estimation guidance for unknown foods instead of failing. |
| `add_meal(food)` | **Official (required)** | Log a food to today's memory, with its calorie value and source (`local_database` or `llm_estimate`). |
| `remove_meal(food)` | Extension (not required by the assignment) | Removes one previously logged meal matching that name, so users can correct mistakes. Added because the teacher's clarification explicitly permits extra tools; the two official tools are unchanged. |

## Memory

`app/memory.py: MemoryStore` keeps an in-process, session-keyed
`DayState` (budget, meals, computed consumed/remaining) for each
`session_id`. It is **not** a database — state is lost if the server
restarts. This is a deliberate, stated limitation appropriate for a CA1
deployment; a persistence layer (SQLite/Redis) would be the natural next
step for a production version.

## Architecture

```
Browser (web/) --fetch /api/*--> FastAPI (api_server.py)
                                      |
                                      v
                              app/agent.py (plan-act loop)
                                 |        |
                        app/tools.py   app/memory.py
                                 |
                              Groq API (gpt-oss-120b / vision model)
```

- `app/config.py` — env-driven configuration (models, limits, CORS).
- `app/tools.py` — the two official tools + `remove_meal`, plus their
  Groq tool-calling JSON schemas.
- `app/agent.py` — the real Groq plan-act loop (`run_agent`) and the
  separate vision-model call (`analyze_food_image`).
- `app/memory.py` — session-scoped state.
- `api_server.py` — FastAPI routes, serves `web/` as static files.
- `web/` — vanilla HTML/CSS/JS frontend (no framework, no build step).
- `main.py` — CLI loop for manually exercising the agent and printing
  the trace.
- `notebooks/CA1_Meal_Calorie_Helper.ipynb` — the required 3 demo runs.

## Agent trace (FEATURE 8)

Every turn returns a `trace` array of structured events so the plan-act
loop is inspectable, e.g.:

```json
{"step": 1, "action": "read_memory", "decision_source": "MEMORY", "result": {...}}
{"step": 2, "action": "tool_call", "decision_source": "LLM", "tool": "lookup_calories", "args": {"food": "banana"}}
{"step": 3, "action": "tool_result", "decision_source": "TOOL", "tool": "lookup_calories", "result": {...}}
{"step": 4, "action": "final_answer", "decision_source": "LLM", "text": "..."}
```

The frontend's "Show trace" panel renders this live for every chat turn.

## Setup

```bash
cd MealTracker
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in GROQ_API_KEY
```

## Environment variables (`.env`)

```
GROQ_API_KEY=...
GROQ_TEXT_MODEL=openai/gpt-oss-120b
GROQ_VISION_MODEL=qwen/qwen3.6-27b
MAX_AGENT_STEPS=8
DEFAULT_CALORIE_BUDGET=2000
MAX_IMAGE_BYTES=6291456
CORS_ALLOW_ORIGINS=*
```

`.env` is git-ignored — never commit real keys.

## Running the backend + frontend

```bash
uvicorn api_server:app --reload --port 8000
```

Then open **http://localhost:8000/** — the FastAPI app serves the
`web/` frontend directly, so there is nothing else to start.

## Running the CLI demo

```bash
python main.py
```

## Running the notebook

```bash
jupyter notebook notebooks/CA1_Meal_Calorie_Helper.ipynb
```

Requires a real `GROQ_API_KEY` in the environment — the notebook makes
live Groq calls (unlike the unit tests, which mock Groq entirely).

## Tests

```bash
pytest tests/ -v
```

No real API key is required — Groq calls are mocked in
`tests/test_agent.py`. 21 tests currently pass, covering both official
tools, `remove_meal` (including duplicate handling), memory isolation
and persistence, and the plan-act loop (direct answers, multi-step tool
loops, memory read-back across turns, and the step-limit safety net).

## Using the image feature

1. Open the app in a browser (camera capture works on supported mobile
   browsers via the file input's `capture="environment"` attribute).
2. In the **Image Analyzer** panel, tap the upload zone and choose/take a
   food photo.
3. Click **Analyze Food** — the image is sent to
   `POST /api/image/analyze` as `multipart/form-data`, which forwards it
   to `GROQ_VISION_MODEL` and returns a structured, approximate estimate.
4. Optionally click **Add recognized foods to today's meals** to log the
   detected items (`POST /api/image/add-foods`) — nothing is added
   automatically.

## API routes

| Route | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Liveness check |
| `/api/state?session_id=` | GET | Current budget/meals/totals |
| `/api/chat` | POST | Run one agent turn (`{session_id, message}`) |
| `/api/budget` | POST | Set today's calorie budget |
| `/api/meals/remove` | POST | Remove one meal by name (frontend button) |
| `/api/image/analyze` | POST | Multipart image upload -> vision analysis |
| `/api/image/add-foods` | POST | Log user-confirmed detected foods |

## Deployment

1. Do not commit `.env`; configure `GROQ_API_KEY` (and other vars) as
   deployment secrets/environment variables on whatever platform is used
   (Render, Railway, Fly.io, a VM, etc.).
2. The frontend calls only relative paths (`/api/...`), so no
   localhost URLs need changing between local and deployed use.
3. Serve with a production ASGI setup, e.g.:
   ```bash
   uvicorn api_server:app --host 0.0.0.0 --port $PORT
   ```
4. `api_server.py` mounts `web/` as static files at `/`, so a single
   deployed service serves both the API and the frontend — no separate
   static host is required.
5. Only enable `CORS_ALLOW_ORIGINS` restrictions if the frontend is ever
   served from a different origin than the API; by default the same
   FastAPI app serves both, so CORS is not strictly needed.

## Known limitations (stated honestly)

- Memory is in-process only; it resets on server restart and does not
  scale across multiple server instances.
- The local calorie table is small by design; unknown foods rely on the
  LLM's own estimate, clearly labelled, rather than a nutrition API.
- Image-based calorie estimates are approximate by nature (portion size
  cannot be reliably measured from a single photo).

---

# CA1 Alignment

**Implementation (10 marks).** Two real tools (`lookup_calories`,
`add_meal`) are called by the LLM through Groq's tool-calling API, not
invoked by keyword matching — verified in `tests/test_agent.py` with a
mocked multi-step tool loop and in the notebook with live calls. A real
multi-step plan-act loop feeds each tool result back to the LLM before it
decides the next action (`app/agent.py: run_agent`). Session memory
(`app/memory.py`) is written by `add_meal`/`remove_meal` and read back on
every subsequent turn, demonstrated by `test_memory_persists_across_
multiple_reads` and Demo 2/3 in the notebook. The teacher's extensions —
`remove_meal`, broader food/meal request handling without a hard-coded
dictionary boundary, a FastAPI + HTML/CSS/JS frontend, and image analysis
via a separate Groq vision model — are all implemented and tested.

**Presentation (10 marks).** A polished, responsive, single-page frontend
(`web/`) presents a live calorie dashboard, a meal list with per-item
remove actions, a chat panel with Markdown-rendered structured
recommendations, an image capture/analyze flow with a confirm-before-add
step, and a togglable agent-trace panel — all built with accessible
controls, `prefers-reduced-motion` support, and no heavy animation
frameworks. The notebook presents three clearly labelled, readable demo
runs with a step-by-step trace printout.

**Viva (10 marks).** The student can point to: the plan-act loop deciding
the next step (`app/agent.py`, the `for _ in range(MAX_AGENT_STEPS)` loop
around `client.chat.completions.create(..., tools=TOOL_SCHEMAS)`); a real
tool call (`app/tools.py: lookup_calories` / `add_meal` / `remove_meal`,
dispatched via `TOOL_FUNCTIONS`); and where memory is read back
(`app/agent.py: memory_store.get_state(session_id)` at the top of
`run_agent`, and the `read_memory` trace event in every turn's output).
