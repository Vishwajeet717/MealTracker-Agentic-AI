"""
API-level tests: every endpoint of api_server.py with the Groq client mocked.
"""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from api_server import app
from app.agent import agent as agent_instance
from app.memory import memory_store


client = TestClient(app)


def _tool_call(call_id, name, arguments: dict):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _response(content=None, tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.call_index = 0

    def create(self, **kwargs):
        response = self._responses[self.call_index]
        self.call_index += 1
        return response


def _fake_client(responses):
    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(responses)))


def _parse_sse(text: str):
    events = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_name = None
        data_lines = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_name = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:"):].strip())
        events.append((event_name, json.loads("\n".join(data_lines))))
    return events


def test_chat_endpoint_returns_full_payload():
    session = str(uuid.uuid4())
    fake = _fake_client([_response(content="Hi there!")])

    with patch.object(agent_instance, "client", fake):
        response = client.post(
            "/api/chat",
            json={"message": "What is the capital of France?", "session_id": ""},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Hi there!"
    assert body["cards"] == []
    assert "trace" in body and "state" in body
    # Empty session id resolves to "default", never a fresh UUID.
    assert body["session_id"] == "default"


def test_chat_stream_happy_path():
    session = str(uuid.uuid4())
    step1 = _response(tool_calls=[_tool_call("c1", "lookup_calories", {"food": "apple"})])
    step2 = _response(content="An apple has about 95 kcal.")
    fake = _fake_client([step1, step2])

    with patch.object(agent_instance, "client", fake):
        response = client.post(
            "/api/chat/stream",
            json={"message": "How many calories are in an apple?", "session_id": session},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(response.text)
    names = [name for name, _payload in events]
    assert names[0] == "trace"
    assert names[-1] == "done"
    assert "error" not in names

    assert events[0][1]["step"] == "read_memory_context"

    done = events[-1][1]
    assert done["reply"] == "An apple has about 95 kcal."
    assert "trace" in done and "state" in done and "session_id" in done
    breakdown = [card for card in done["cards"] if card["type"] == "breakdown"]
    assert breakdown and breakdown[0]["total"] == 95


def test_chat_stream_error_event():
    session = str(uuid.uuid4())

    with patch.object(
        agent_instance, "get_memory_context", side_effect=RuntimeError("boom")
    ):
        response = client.post(
            "/api/chat/stream",
            json={"message": "How many calories are in an apple?", "session_id": session},
        )

    events = _parse_sse(response.text)
    assert events[-1][0] == "error"
    assert "boom" in events[-1][1]["message"]


def test_reset_clears_session_state():
    session = str(uuid.uuid4())
    memory_store.set_budget(session, 1800)
    memory_store.add_meal(session_id=session, food="apple", calories=95)

    response = client.post("/api/reset", json={"session_id": session})

    assert response.status_code == 200
    state = response.json()["state"]
    assert state["budget"] is None
    assert state["meals"] == []
    assert state["consumed"] == 0


def test_meal_endpoints_add_and_remove():
    session = str(uuid.uuid4())

    response = client.post(
        "/api/meals", json={"session_id": session, "food": "Apple", "calories": 95}
    )
    body = response.json()
    assert body["added"] is True
    assert body["state"]["consumed"] == 95

    # Calories omitted -> resolved from the local database.
    response = client.post("/api/meals", json={"session_id": session, "food": "banana"})
    body = response.json()
    assert body["added"] is True
    assert body["state"]["consumed"] == 200

    # Unknown food without calories -> rejected with a message.
    # ("dragon fruit" deliberately avoids any substring of the database.)
    response = client.post(
        "/api/meals", json={"session_id": session, "food": "dragon fruit"}
    )
    body = response.json()
    assert body["added"] is False
    assert body["message"]

    response = client.delete(f"/api/meals?session_id={session}&food=apple")
    assert response.json()["removed"] is True
    assert response.json()["state"]["consumed"] == 105

    response = client.delete(f"/api/meals?session_id={session}&food=apple")
    assert response.json()["removed"] is False


def test_state_endpoint_uses_default_session():
    response = client.get("/api/state", params={"session_id": ""})
    assert response.status_code == 200
    assert "consumed" in response.json()
