from dataclasses import dataclass, field
from datetime import date
from threading import Lock
from typing import Optional


@dataclass
class Meal:
    food: str
    calories: float
    estimated: bool = False
    source: str = "local"


@dataclass
class SessionMemory:
    budget: Optional[float] = None
    meals: list[Meal] = field(default_factory=list)
    day: date = field(default_factory=date.today)


class MemoryStore:
    def __init__(self):
        self._sessions: dict[str, SessionMemory] = {}
        self._lock = Lock()

    def _get_session(self, session_id: str) -> SessionMemory:
        today = date.today()

        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(day=today)

        session = self._sessions[session_id]

        # Automatically reset on a new day
        if session.day != today:
            session.budget = None
            session.meals.clear()
            session.day = today

        return session

    def get(self, session_id: str) -> SessionMemory:
        with self._lock:
            return self._get_session(session_id)

    def reset(self, session_id: str) -> None:
        with self._lock:
            session = self._get_session(session_id)
            session.budget = None
            session.meals.clear()

    def set_budget(self, session_id: str, budget: float) -> SessionMemory:
        with self._lock:
            session = self._get_session(session_id)
            session.budget = float(budget)
            return session

    def add_meal(
        self,
        session_id: str,
        food: str,
        calories: float,
        estimated: bool = False,
        source: str = "local",
    ) -> SessionMemory:
        with self._lock:
            session = self._get_session(session_id)

            session.meals.append(
                Meal(
                    food=food,
                    calories=float(calories),
                    estimated=estimated,
                    source=source,
                )
            )

            return session

    def remove_meal(
        self,
        session_id: str,
        food: str,
    ) -> tuple[bool, Optional[Meal]]:

        with self._lock:
            session = self._get_session(session_id)

            food_lower = food.lower().strip()

            for index, meal in enumerate(session.meals):
                if meal.food.lower().strip() == food_lower:
                    removed = session.meals.pop(index)
                    return True, removed

            return False, None

    def total_calories(self, session_id: str) -> float:
        session = self.get(session_id)
        return round(sum(meal.calories for meal in session.meals), 2)

    def remaining_calories(self, session_id: str) -> Optional[float]:
        session = self.get(session_id)

        if session.budget is None:
            return None

        return round(
            session.budget - self.total_calories(session_id),
            2,
        )

    def summary(self, session_id: str) -> dict:
        session = self.get(session_id)

        total = self.total_calories(session_id)
        remaining = self.remaining_calories(session_id)

        return {
            "budget": session.budget,
            "consumed": total,
            "remaining": remaining,
            "meal_count": len(session.meals),
            "meals": [
                {
                    "food": meal.food,
                    "calories": meal.calories,
                    "estimated": meal.estimated,
                    "source": meal.source,
                }
                for meal in session.meals
            ],
        }


memory_store = MemoryStore()