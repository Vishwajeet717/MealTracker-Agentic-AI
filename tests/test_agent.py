"""
Tests for the streaming plan-act loop in app/agent.py.

Groq itself is always mocked here — pytest must never require a real
GROQ_API_KEY or make a network call.
"""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from app import agent as agent_module
from app.agent import agent as agent_instance
from app.memory import memory_store


def _tool_call(call_id, name, arguments: dict):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _response(content=None, tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


class FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.call_index = 0
        self.calls = []

    def create(self, **kwargs):
        if self.call_index >= len(self._responses):
            raise AssertionError("FakeCompletions ran out of responses")
        # Copy the message list: the agent mutates it in place between
        # calls (the single-snapshot refresh), so capturing by reference
        # would show every call the final state.
        captured = {
            key: ([dict(message) for message in value] if key == "messages" else value)
            for key, value in kwargs.items()
        }
        self.calls.append(captured)
        response = self._responses[self.call_index]
        self.call_index += 1
        return response


class ExplodingCompletions:
    def create(self, **kwargs):
        raise RuntimeError("network down")


def _fake_client(responses):
    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(responses)))


def _memory_content(messages):
    """Return the content of the single CURRENT MEMORY snapshot message.

    The main system prompt also mentions "CURRENT MEMORY", so match the
    message that *is* the snapshot (it starts with the marker).
    """
    found = [
        m["content"]
        for m in messages
        if m["role"] == "system" and m["content"].startswith("CURRENT MEMORY:")
    ]
    assert len(found) == 1, f"expected exactly one memory snapshot, got {len(found)}"
    return found[0].split("CURRENT MEMORY:\n\n", 1)[1]


def test_direct_answer_no_tools():
    """LLM decides no tool is needed and answers straight away."""
    session = str(uuid.uuid4())
    fake = _fake_client([_response(content="I can help with meals and calories.")])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("What is the capital of France?", session)

    assert result["answer"] == "I can help with meals and calories."
    assert result["cards"] == []
    steps = [step["step"] for step in result["trace"]]
    assert steps[0] == "read_memory_context"
    assert steps[-1] == "final_answer"
    assert fake.chat.completions.call_index == 1


def test_stream_yields_steps_then_done():
    session = str(uuid.uuid4())
    fake = _fake_client([_response(content="Hello!")])

    with patch.object(agent_instance, "client", fake):
        events = list(agent_instance.run_stream("What is the capital of France?", session))

    kinds = [kind for kind, _payload in events]
    assert kinds[0] == "trace"
    assert kinds[-1] == "done"

    first_trace = events[0][1]
    assert first_trace["step"] == "read_memory_context"

    done = events[-1][1]
    assert done["answer"] == "Hello!"
    assert done["cards"] == []
    assert done["session_id"] == session
    assert "state" in done


def test_multi_step_tool_loop_logs_meal():
    """lookup_calories -> add_meal -> final answer, with a meal card."""
    session = str(uuid.uuid4())
    step1 = _response(tool_calls=[_tool_call("call_1", "lookup_calories", {"food": "banana"})])
    step2 = _response(
        tool_calls=[
            _tool_call(
                "call_2",
                "add_meal",
                {"food": "banana", "calories": 105, "source": "local_database"},
            )
        ]
    )
    step3 = _response(content="Logged your banana.")
    fake = _fake_client([step1, step2, step3])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("I had a banana.", session)

    steps = [step["step"] for step in result["trace"]]
    assert steps.count("tool_call") == 2
    assert steps.count("tool_result") == 2
    assert steps[-1] == "final_answer"
    assert result["state"]["consumed"] == 105
    assert fake.chat.completions.call_index == 3

    meal_cards = [card for card in result["cards"] if card["type"] == "meal_logged"]
    assert len(meal_cards) == 1
    assert meal_cards[0]["food"] == "banana"
    assert meal_cards[0]["calories"] == 105
    assert meal_cards[0]["consumed"] == 105


def test_lookup_only_builds_breakdown_card_without_budget():
    """Two lookups, no add -> breakdown card with verdict 'unknown'."""
    session = str(uuid.uuid4())
    step1 = _response(tool_calls=[_tool_call("c1", "lookup_calories", {"food": "apple"})])
    step2 = _response(tool_calls=[_tool_call("c2", "lookup_calories", {"food": "yogurt"})])
    step3 = _response(content="That snack is about 215 kcal.")
    fake = _fake_client([step1, step2, step3])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("Can I have an apple and yogurt as a snack?", session)

    breakdown = next(card for card in result["cards"] if card["type"] == "breakdown")
    assert breakdown["total"] == 215
    assert breakdown["verdict"] == "unknown"
    assert breakdown["remaining_before"] is None
    assert breakdown["remaining_after"] is None
    assert [item["food"] for item in breakdown["items"]] == ["apple", "yogurt"]


def test_breakdown_verdict_fits_with_budget():
    session = str(uuid.uuid4())
    memory_store.set_budget(session, 2000)
    step1 = _response(tool_calls=[_tool_call("c1", "lookup_calories", {"food": "apple"})])
    step2 = _response(tool_calls=[_tool_call("c2", "lookup_calories", {"food": "yogurt"})])
    step3 = _response(content="Fits comfortably.")
    fake = _fake_client([step1, step2, step3])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("Can I have an apple and yogurt as a snack?", session)

    breakdown = next(card for card in result["cards"] if card["type"] == "breakdown")
    assert breakdown["verdict"] == "fits"
    assert breakdown["remaining_before"] == 2000
    assert breakdown["remaining_after"] == 1785


def test_breakdown_verdict_over_budget():
    session = str(uuid.uuid4())
    memory_store.set_budget(session, 100)
    step1 = _response(tool_calls=[_tool_call("c1", "lookup_calories", {"food": "pizza"})])
    step2 = _response(content="That would exceed your budget.")
    fake = _fake_client([step1, step2])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("Can I have pizza as a snack?", session)

    breakdown = next(card for card in result["cards"] if card["type"] == "breakdown")
    assert breakdown["verdict"] == "over"
    assert breakdown["remaining_after"] == -185


def test_budget_set_card():
    session = str(uuid.uuid4())
    step1 = _response(tool_calls=[_tool_call("c1", "set_calorie_budget", {"budget": 2000})])
    step2 = _response(content="Goal saved.")
    fake = _fake_client([step1, step2])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("My calorie budget is 2000 calories.", session)

    card = next(card for card in result["cards"] if card["type"] == "budget_set")
    assert card["budget"] == 2000
    assert card["remaining"] == 2000


def test_memory_snapshot_refreshed_in_place():
    """Exactly one CURRENT MEMORY system message, always showing the
    latest state — the fix for stale 'consumed 0' prose numbers."""
    session = str(uuid.uuid4())
    step1 = _response(tool_calls=[_tool_call("c1", "lookup_calories", {"food": "banana"})])
    step2 = _response(
        tool_calls=[_tool_call("c2", "add_meal", {"food": "banana", "calories": 105})]
    )
    step3 = _response(content="Logged.")
    fake = _fake_client([step1, step2, step3])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("I had a banana.", session)

    calls = fake.chat.completions.calls
    assert len(calls) == 3

    # Call 1: initial state. Call 2: after the lookup round (unchanged).
    # Call 3: after add_meal — the refreshed snapshot must show the meal.
    first_memory = json.loads(_memory_content(calls[0]["messages"]))
    second_memory = json.loads(_memory_content(calls[1]["messages"]))
    third_memory = json.loads(_memory_content(calls[2]["messages"]))
    assert first_memory["consumed"] == 0
    assert second_memory["consumed"] == 0
    assert third_memory["consumed"] == 105

    for call in calls:
        assert not any(
            "UPDATED CURRENT MEMORY" in message["content"]
            for message in call["messages"]
            if message["role"] == "system"
        )


def test_step_limit_returns_system_limit(monkeypatch):
    """If the LLM never stops requesting tools, the loop must end safely."""
    monkeypatch.setattr(agent_module, "MAX_AGENT_STEPS", 2)
    session = str(uuid.uuid4())
    looping = _response(tool_calls=[_tool_call("cx", "lookup_calories", {"food": "banana"})])
    fake = _fake_client([looping, looping, looping])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("keep looking things up", session)

    final = result["trace"][-1]
    assert final["step"] == "final_answer"
    assert final["decision_source"] == "SYSTEM_LIMIT"


def test_trace_steps_are_numbered_and_timed():
    session = str(uuid.uuid4())
    step1 = _response(tool_calls=[_tool_call("c1", "lookup_calories", {"food": "apple"})])
    step2 = _response(content="An apple has about 95 kcal.")
    fake = _fake_client([step1, step2])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("How many calories are in an apple?", session)

    trace = result["trace"]
    assert [step["id"] for step in trace] == [
        f"s{index}" for index in range(1, len(trace) + 1)
    ]
    timestamps = [step["ts"] for step in trace]
    assert timestamps == sorted(timestamps)
    assert all("duration_ms" in step for step in trace if step["step"] == "agent_iteration")
    assert all("duration_ms" in step for step in trace if step["step"] == "tool_result")


def test_empty_message_returns_done_without_llm_call():
    session = str(uuid.uuid4())
    fake = _fake_client([_response(content="unused")])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("   ", session)

    assert result["trace"] == []
    assert result["cards"] == []
    assert fake.chat.completions.call_index == 0


def test_irrelevant_message_short_circuits():
    session = str(uuid.uuid4())
    fake = _fake_client([_response(content="unused")])

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("Write me a python function", session)

    assert [step["step"] for step in result["trace"]] == ["scope_check"]
    assert fake.chat.completions.call_index == 0


def test_llm_error_yields_fallback_answer():
    session = str(uuid.uuid4())
    fake = SimpleNamespace(
        chat=SimpleNamespace(completions=ExplodingCompletions())
    )

    with patch.object(agent_instance, "client", fake):
        result = agent_instance.run("I had rice for lunch.", session)

    steps = [step["step"] for step in result["trace"]]
    assert "llm_error" in steps
    assert "couldn't connect" in result["answer"]
