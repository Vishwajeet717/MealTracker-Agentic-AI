import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import agent
from app.memory import memory_store
from app.tools import add_meal, remove_meal


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"


app = FastAPI(
    title="Meal Calorie Helper",
    version="2.0.0",
)


app.mount(
    "/static",
    StaticFiles(directory=WEB_DIR),
    name="static",
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class BudgetRequest(BaseModel):
    budget: float
    session_id: str = "default"


class ResetRequest(BaseModel):
    session_id: str = "default"


class MealRequest(BaseModel):
    session_id: str = "default"
    food: str
    calories: float | None = None
    estimated: bool = False


def _session_id(value: str | None) -> str:
    # Never mint a fresh UUID per request: an unknown or empty session
    # resolves to "default" so state stays consistent for that client.
    return value if value else "default"


@app.get("/")
def home():
    return FileResponse(
        WEB_DIR / "index.html"
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Meal Calorie Helper",
    }


@app.get("/api/state")
def get_state(session_id: str = "default"):
    return memory_store.summary(_session_id(session_id))


@app.post("/api/chat")
def chat(request: ChatRequest):
    session_id = _session_id(request.session_id)

    result = agent.run(
        user_message=request.message,
        session_id=session_id,
    )

    return {
        "reply": result["answer"],
        "trace": result["trace"],
        "cards": result["cards"],
        "state": result["state"],
        "session_id": session_id,
    }


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    session_id = _session_id(request.session_id)

    def event_stream():
        try:
            for kind, payload in agent.run_stream(
                user_message=request.message,
                session_id=session_id,
            ):
                if kind == "trace":
                    yield f"event: trace\ndata: {json.dumps(payload, default=str)}\n\n"
                elif kind == "done":
                    body = {
                        "reply": payload["answer"],
                        "trace": payload["trace"],
                        "cards": payload["cards"],
                        "state": payload["state"],
                        "session_id": payload["session_id"],
                    }
                    yield f"event: done\ndata: {json.dumps(body, default=str)}\n\n"
        except Exception as exc:
            yield (
                "event: error\n"
                f"data: {json.dumps({'message': str(exc)}, default=str)}\n\n"
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/reset")
def reset(request: ResetRequest):
    session_id = _session_id(request.session_id)
    memory_store.reset(session_id)
    return {"state": memory_store.summary(session_id)}


@app.post("/api/meals")
def add_meal_endpoint(request: MealRequest):
    session_id = _session_id(request.session_id)

    result = add_meal(
        session_id=session_id,
        food=request.food,
        calories=request.calories,
        estimated=request.estimated,
        source="manual entry",
    )

    return {
        "added": bool(result.get("success")),
        "message": result.get("message"),
        "state": memory_store.summary(session_id),
    }


@app.delete("/api/meals")
def remove_meal_endpoint(session_id: str = "default", food: str = ""):
    session_id = _session_id(session_id)

    removed, _meal = memory_store.remove_meal(
        session_id=session_id,
        food=food,
    )

    return {
        "removed": removed,
        "state": memory_store.summary(session_id),
    }


@app.post("/api/budget")
def update_budget(request: BudgetRequest):
    session_id = _session_id(request.session_id)

    result = agent.run(
        user_message=(
            f"Set my daily calorie budget to "
            f"{request.budget} calories."
        ),
        session_id=session_id,
    )

    return {
        "reply": result["answer"],
        "trace": result["trace"],
        "cards": result["cards"],
        "state": result["state"],
        "session_id": session_id,
    }
