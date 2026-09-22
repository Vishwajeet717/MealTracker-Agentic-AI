# CA1 Rubric Checklist — T17 Meal Calorie Helper

## Implementation — 10 marks

- [x] One working AI agent: `app/agent.py` uses Groq.
- [x] Real plan–act loop: the LLM selects tool calls; results are returned to the LLM for the next decision.
- [x] At least two working tools: `lookup_calories(food)` and `add_meal(food)`.
- [x] Tools are actually called: the notebook/CLI trace records `decision_source: LLM` for tool calls.
- [x] Memory: `SessionMemory` stores today's budget and meals.
- [x] Memory reused later: each user turn receives the current memory summary; updated memory is re-injected after tool execution.

## Presentation — 10 marks

- [x] Notebook with 3 demonstrations.
- [x] Notebook prints final answers and the multi-step agent trace.
- [x] README names both tools, explains memory, and documents one honest limitation/failure boundary.
- [x] Frontend exposes the agent and an expandable trace for demonstration.
- [ ] Final live deployment URL — add after Streamlit Community Cloud deployment.

## Viva — 10 marks

### Where does the plan–act loop happen?
`app/agent.py`, inside `MealCalorieAgent.run()`: Groq is called with the tool schemas, the returned `message.tool_calls` are inspected, tools are executed, their results are appended, memory is refreshed, and Groq is called again.

### Where are the two tools?
`app/tools.py`: `lookup_calories()` and `add_meal()`.

### Where is memory?
`app/memory.py`: `SessionMemory` stores the budget and meal list.

### Where is memory read back?
`app/agent.py`: `_memory_context()` / `get_memory_summary()` is added to the LLM context at the start of every turn and again after tool execution.

### What makes this an agent rather than a chatbot?
The LLM selects actions from tool schemas, observes real tool results, chooses whether to take another action, uses persistent session state from earlier turns, and only then gives its final answer.

## Final validation before submission

- [ ] Run `python -m pytest` with all tests passing.
- [ ] Run the notebook from a fresh kernel and capture successful outputs.
- [ ] Test at least one unknown/unusual food; it must still be handled with an estimate.
- [ ] Test one clearly irrelevant request; it should be rejected politely.
- [ ] Run the Streamlit frontend locally.
- [ ] Deploy to Streamlit Community Cloud.
- [ ] Add the deployed URL to the project README and final presentation.
