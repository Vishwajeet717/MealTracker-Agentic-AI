"""Tests for app/tools.py — lookup_calories, add_meal, remove_meal, budget."""

import uuid

from app.memory import memory_store
from app.tools import add_meal, lookup_calories, remove_meal, set_calorie_budget


def new_session() -> str:
    return f"test-{uuid.uuid4()}"


# ---------------------------------------------------------------------
# lookup_calories
# ---------------------------------------------------------------------
def test_lookup_known_food():
    result = lookup_calories("banana")
    assert result["found"] is True
    assert result["calories"] == 105
    assert result["estimated"] is False
    assert result["source"] == "educational local database"


def test_lookup_unknown_food_does_not_fail_hard():
    """Unknown food must not be a hard failure — it signals the LLM to
    estimate instead. ("dragon fruit" avoids any fuzzy substring match.)"""
    result = lookup_calories("dragon fruit")
    assert result["found"] is False
    assert result["calories"] is None
    assert "estimate" in result["message"].lower()


def test_lookup_fuzzy_match():
    result = lookup_calories("plain oatmeal")
    assert result["found"] is True
    assert result["estimated"] is True
    assert result["source"] == "approximate database match"


# ---------------------------------------------------------------------
# add_meal
# ---------------------------------------------------------------------
def test_add_meal_with_known_calories():
    session = new_session()
    result = add_meal(session, food="banana", calories=105)
    assert result["success"] is True
    assert result["total_consumed"] == 105
    assert len(memory_store.summary(session)["meals"]) == 1


def test_add_meal_uses_given_estimate_for_unknown_food():
    session = new_session()
    result = add_meal(
        session, food="quantum croissant", calories=480, estimated=True,
        source="llm estimate",
    )
    assert result["success"] is True
    assert result["estimated"] is True
    assert result["source"] == "llm estimate"


def test_add_meal_falls_back_to_lookup_when_calories_missing():
    session = new_session()
    result = add_meal(session, food="apple")
    assert result["success"] is True
    assert result["calories"] == 95


def test_add_meal_fails_cleanly_when_unknown_and_no_calories_given():
    session = new_session()
    result = add_meal(session, food="totally novel dish xyz")
    assert result["success"] is False
    assert "message" in result
    assert memory_store.summary(session)["meals"] == []


def test_remaining_budget_updates_after_add():
    session = new_session()
    memory_store.set_budget(session, 2000)
    add_meal(session, food="banana", calories=105)
    assert memory_store.summary(session)["remaining"] == 1895


# ---------------------------------------------------------------------
# remove_meal
# ---------------------------------------------------------------------
def test_remove_meal_success():
    session = new_session()
    add_meal(session, food="banana", calories=105)
    result = remove_meal(session, food="banana")
    assert result["success"] is True
    assert result["removed_calories"] == 105
    assert result["total_consumed"] == 0


def test_remove_meal_unknown_food_does_not_corrupt_memory():
    session = new_session()
    add_meal(session, food="banana", calories=105)
    result = remove_meal(session, food="pizza")
    assert result["success"] is False
    assert len(memory_store.summary(session)["meals"]) == 1  # untouched


def test_remove_meal_removes_only_one_duplicate():
    session = new_session()
    add_meal(session, food="banana", calories=105)
    add_meal(session, food="banana", calories=105)
    result = remove_meal(session, food="banana")
    assert result["success"] is True
    summary = memory_store.summary(session)
    assert summary["meal_count"] == 1
    assert summary["meals"][0]["food"] == "banana"


def test_remove_meal_case_insensitive():
    session = new_session()
    add_meal(session, food="Banana", calories=105)
    assert remove_meal(session, food="banana")["success"] is True


# ---------------------------------------------------------------------
# set_calorie_budget
# ---------------------------------------------------------------------
def test_set_budget_rejects_non_positive():
    session = new_session()
    assert set_calorie_budget(session, 0)["success"] is False
    assert set_calorie_budget(session, -500)["success"] is False
    assert memory_store.summary(session)["budget"] is None


def test_set_budget_updates_memory():
    session = new_session()
    result = set_calorie_budget(session, 2000)
    assert result["success"] is True
    assert memory_store.summary(session)["budget"] == 2000
