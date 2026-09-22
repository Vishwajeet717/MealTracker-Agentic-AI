# MealTracker UI/UX Redesign — Implementation Plan

## Step 0 — Install the design skills (first action; couldn't run in plan mode)
- `npx impeccable install` (pbakaus/impeccable — design audit/redesign/polish lenses)
- `npx skills add https://github.com/emilkowalski/skills --skill apple-design` (Apple fluid motion for web)
- `npx skills add https://github.com/dickwu/apple-design-skill --skill apple-design` (HIG-grounded reviewer with 122 HIG reference pages)
- Note: both repos install a skill named `apple-design`. Install emil's first, dickwu's second; if the second overwrites, keep both bodies under distinct folders (dickwu's = HIG audit lens, emil's = motion lens). Their guidance is applied in every step below.

## Step 1 — Design audit findings (from screenshots + code exploration)
**Chat has no visual impact:** `formatText` (web/app.js:17-19) only renders bold/headings — the model's ASCII pipe-tables (`| Food | Calories |`) dump as ragged plain text. The system prompt (app/agent.py:418-432) never forbids tables. Full reply appears at once behind a fake "Thinking…" bubble; no streaming.
**Not live:** no SSE anywhere; trace re-renders wholesale via innerHTML only after everything finishes (slice(-10)); "Ready"/"Live" pills are static decoration (never referenced in app.js); panels update only after the full round-trip; numbers jump with no animation.
**Agent trace not lucid:** every step is an identical hollow circle (styles.css `:before`), no pending/active/done states, no icons, timestamps, or durations; generic repeated labels ("Considering your request" ×3); payloads only on hover; silently truncated to last 10 steps.
**Bugs/quality:** Reset button never resets server state (no reset tool/route — server keeps 500 kcal while UI clears); chat said "consumed 0 kcal" while sidebar showed 500 (stale duplicate memory snapshots in the LLM context, agent.py:808/1091); api_server.py:63-64 mints a fresh session UUID on empty id; styles.css minified to one line; 3 dead backup JS files publicly served from web/.

## Step 2 — Design foundation (Apple-neutral re-theme, vanilla restructure)
- Rewrite `web/styles.css` un-minified and token-based: graphite/neutral surfaces (light: #f5f5f7 bg + white cards; dark: true black + #1c1c1e elevated), one restrained accent (iOS blue #007AFF/#0A84FF) reserved for interactive elements, semantic colors for the ring (green→amber→red), explicit type ramp (11/13/15/17/22/28 pt, SF system stack), 4/8pt spacing, radii 10/14/18/24, hairline semi-transparent separators, layered shadows.
- Motion tokens: Apple sheet easing cubic-bezier(0.32,0.72,0,1), durations 150/250/400/550ms; `prefers-reduced-motion` honored everywhere.
- Manual theme toggle (auto/light/dark, persisted) on top of `prefers-color-scheme`.
- Restructure JS into `web/js/` ES modules: `api.js`, `markdown.js`, `chat.js`, `cards.js`, `trace.js`, `panels.js`, `toast.js`, `main.js`. Delete served dead files (`app.js.backup/.restored/.bak2`).
- Keep the 3-column layout skeleton and existing panel semantics; same SVG ring centerpiece, refined.

## Step 3 — Chat: give responses visual impact (headline)
- Vendor `marked` + `DOMPurify` into `web/vendor/` (local files, no CDN at runtime): real markdown rendering — styled tables, lists, bold, links — as the safety net.
- **Structured nutrition cards:** backend attaches a `cards` array to each response, computed deterministically from tool results + memory diff (not model prose): breakdown card (food rows with kcal, total row, verdict banner "Fits your budget" green / "Over budget" amber with icon), meal-logged card, budget-set card. Frontend renders these as native animated cards; markdown text stays as fallback. This kills the pipe-table problem at the source.
- System prompt "FINAL ANSWERS" (agent.py:418-432): forbid ASCII/markdown pipe tables; require short bold/lists, concise numbers quoted from the LATEST memory block only.
- Animated answer reveal (per your choice — no token typewriter): the complete answer appears as one polished entrance — fade+rise with staggered card/row animations and a subtle verdict highlight sweep.

## Step 4 — Real live trace via SSE
- `app/agent.py`: refactor `run()` into a `run_stream()` generator yielding events as they actually happen — every trace step (`read_memory_context`, `agent_iteration`, `tool_call`, `tool_result`, `final_answer`, errors) plus per-step timestamps/durations and the final `{answer, cards, state}`. Keep `run()` as a wrapper so tests and the CLI keep working.
- `api_server.py`: add `POST /api/chat/stream` returning `text/event-stream` (`trace` events, `done` event). Existing `POST /api/chat` stays unchanged.
- Frontend: consumes the stream via fetch-ReadableStream; the Activity panel populates in real time; the status pill becomes real ("Thinking…" → current tool action → "Ready"); thinking bubble shows a live step label ("Checking calories for aloo paratha…"). Final answer renders on `done` with the Step 3 reveal; side panels update with animated count-ups.

## Step 5 — Agent trace redesign (lucid)
- Status-driven nodes: done (filled check), active (pulsing ring), error (red); per-tool SVG icons (lookup = magnifier, add_meal = plus, budget = target, memory = book).
- Group each `tool_call`+`tool_result` pair into one row; collapse consecutive `agent_iteration`s; expandable monospace payload chip (truncated, `<details>` expander, copy button).
- Header shows step count + total duration; "Show earlier steps" expander replaces silent slice(-10); connector line draws as steps arrive.

## Step 6 — Interaction & micro-interactions
- Animated count-ups for budget/consumed/remaining; gradient ring with soft glow, animated stroke, threshold colors; bar tween.
- Sonner-style toasts: "Aloo paratha added · Undo" (undo calls remove), "Goal updated".
- Meals list: entrance animations, hover-reveal remove button; "+ Add a meal" opens an inline mini-form (food + optional kcal) instead of just prefilling the composer.
- Contextual quick-action chips that adapt to state (no budget yet → "Set a goal"; else "Plan a snack", "What fits for dinner?"); follow-up chips under each answer ("Log it", "Adjust").
- Composer: auto-growing textarea, Enter send / Shift+Enter newline, Esc to cancel an in-flight run, clear focus rings; `/` focuses composer.

## Step 7 — Bug fixes surfaced by the audit
- Add server-side reset (`/api/reset` + memory-store reset); Reset button calls it.
- Fix consumed-inconsistency: maintain a single up-to-date memory system message (replace rather than append snapshots) and drive all numbers in cards from state, not prose.
- Don't mint a fresh UUID per empty session_id (api_server.py:63-64).
- Remove the publicly served backup JS files.

## Step 8 — Verification
- Run existing pytest suite; add tests for the stream endpoint, reset, and cards payload.
- Launch uvicorn and exercise the app with browser automation: snack query (live trace + card reveal), log meal (toast, count-up, undo), set budget, reset; capture desktop + narrow viewport, dark + light.
- Visual gate: render key states to PNG and dispatch the visual-judge agent for acceptance; repair and re-render until it passes.

**Files touched:** `web/index.html`, `web/styles.css` (rewrite), `web/js/*.js` (new), `web/vendor/*` (new), `app/agent.py`, `api_server.py`, `app/memory.py`, `tests/`.

**Acceptance criteria:** nutrition answers render as rich cards/tables (never ASCII pipe soup); the trace animates in real time with states, icons and durations; numbers animate and panels never contradict the chat text; toasts + undo work; light/dark both polished; reduced-motion and keyboard access honored.