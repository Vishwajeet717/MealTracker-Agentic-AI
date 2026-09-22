"""Tests for app/memory.py — session isolation, persistence, and reset."""

import uuid
from datetime import date, timedelta

from app.memory import MemoryStore


def test_new_session_starts_empty():
    store = MemoryStore()
    session = store.get("s1")
    assert session.budget is None
    assert session.meals == []

    summary = store.summary("s1")
    assert summary["budget"] is None
    assert summary["remaining"] is None
    assert summary["consumed"] == 0


def test_sessions_are_isolated():
    store = MemoryStore()
    store.add_meal("s1", food="banana", calories=105)
    assert store.summary("s2")["meals"] == []
    assert len(store.summary("s1")["meals"]) == 1


def test_memory_persists_across_multiple_reads():
    """Memory written on an earlier turn must be intact on a later read."""
    store = MemoryStore()
    session = str(uuid.uuid4())
    store.set_budget(session, 1800)
    store.add_meal(session, food="oatmeal", calories=158)
    store.add_meal(session, food="banana", calories=105)

    summary = store.summary(session)
    assert summary["budget"] == 1800
    assert summary["consumed"] == 263
    assert summary["remaining"] == 1800 - 263
    assert [meal["food"] for meal in summary["meals"]] == ["oatmeal", "banana"]


def test_remove_meal_recomputes_totals():
    store = MemoryStore()
    session = "s-remove"
    store.add_meal(session, food="banana", calories=105)
    store.add_meal(session, food="apple", calories=95)

    removed, meal = store.remove_meal(session, food="apple")
    assert removed is True
    assert meal.food == "apple"

    summary = store.summary(session)
    assert summary["consumed"] == 105
    assert summary["meal_count"] == 1


def test_reset_clears_budget_and_meals():
    store = MemoryStore()
    session = "s-reset"
    store.set_budget(session, 2000)
    store.add_meal(session, food="banana", calories=105)

    store.reset(session)

    summary = store.summary(session)
    assert summary["budget"] is None
    assert summary["meals"] == []
    assert summary["consumed"] == 0


def test_session_resets_on_a_new_day():
    store = MemoryStore()
    session = "s-midnight"
    store.set_budget(session, 2000)
    store.add_meal(session, food="banana", calories=105)

    # Simulate the session having been created yesterday.
    store.get(session).day = date.today() - timedelta(days=1)

    summary = store.summary(session)
    assert summary["budget"] is None
    assert summary["meals"] == []


def test_totals_are_rounded():
    store = MemoryStore()
    store.add_meal("s-round", food="odd", calories=100.555)
    assert store.summary("s-round")["consumed"] == 100.56
