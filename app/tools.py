from typing import Optional

from .memory import memory_store


# ============================================================
# EDUCATIONAL CALORIE DATABASE
# ============================================================

CALORIE_DATABASE = {
    "apple": 95,
    "banana": 105,
    "orange": 62,
    "mango": 135,
    "grapes": 104,
    "strawberries": 49,
    "blueberries": 84,

    "oatmeal": 158,
    "oats": 158,
    "rice": 205,
    "brown rice": 215,
    "roti": 120,
    "chapati": 120,
    "bread": 80,
    "toast": 80,

    "egg": 78,
    "boiled egg": 78,
    "omelette": 180,
    "chicken breast": 284,
    "grilled chicken": 250,
    "fish": 220,

    "milk": 122,
    "yogurt": 120,
    "curd": 120,
    "greek yogurt": 100,

    "paneer": 265,
    "dal": 180,
    "lentils": 180,

    "pizza": 285,
    "burger": 550,
    "sandwich": 350,
    "fries": 365,

    "idli": 58,
    "dosa": 168,
    "samosa": 262,
    "poha": 180,
    "upma": 200,

    "chocolate": 210,
    "ice cream": 210,
    "cake": 350,
    "cheesecake": 400,
}


# ============================================================
# LOOKUP CALORIES
# ============================================================

def lookup_calories(food: str) -> dict:

    key = food.lower().strip()

    if key in CALORIE_DATABASE:

        return {
            "found": True,
            "food": food,
            "calories": CALORIE_DATABASE[key],
            "estimated": False,
            "source": "educational local database",
        }

    # Approximate matching
    for known_food, calories in CALORIE_DATABASE.items():

        if (
            known_food in key
            or key in known_food
        ):

            return {
                "found": True,
                "food": food,
                "calories": calories,
                "estimated": True,
                "source": "approximate database match",
            }

    return {
        "found": False,
        "food": food,
        "calories": None,
        "estimated": True,
        "source": None,
        "message": (
            "Food was not found in the local database. "
            "Use a reasonable approximate calorie estimate "
            "and clearly mark it as estimated."
        ),
    }


# ============================================================
# ADD MEAL
# ============================================================

def add_meal(
    session_id: str,
    food: str,
    calories: Optional[float] = None,
    estimated: bool = False,
    source: str = "agent estimate",
) -> dict:

    if calories is None:

        lookup = lookup_calories(food)

        if not lookup["found"]:

            return {
                "success": False,
                "food": food,
                "message": (
                    "No calorie value was found. "
                    "Provide an approximate calorie value "
                    "before adding this food."
                ),
            }

        calories = lookup["calories"]
        estimated = lookup["estimated"]
        source = lookup["source"]

    memory_store.add_meal(
        session_id=session_id,
        food=food,
        calories=float(calories),
        estimated=estimated,
        source=source,
    )

    total = memory_store.total_calories(
        session_id
    )

    remaining = memory_store.remaining_calories(
        session_id
    )

    return {
        "success": True,
        "food": food,
        "calories": float(calories),
        "estimated": estimated,
        "source": source,
        "total_consumed": total,
        "remaining": remaining,
    }


# ============================================================
# REMOVE MEAL
# ============================================================

def remove_meal(
    session_id: str,
    food: str,
) -> dict:

    removed, meal = memory_store.remove_meal(
        session_id=session_id,
        food=food,
    )

    if not removed or meal is None:

        return {
            "success": False,
            "food": food,
            "message": (
                f"{food} was not found in today's meals."
            ),
        }

    total = memory_store.total_calories(
        session_id
    )

    remaining = memory_store.remaining_calories(
        session_id
    )

    return {
        "success": True,
        "food": meal.food,
        "removed_calories": meal.calories,
        "total_consumed": total,
        "remaining": remaining,
    }


# ============================================================
# SET CALORIE BUDGET
# ============================================================

def set_calorie_budget(
    session_id: str,
    budget: float,
) -> dict:

    budget = float(budget)

    if budget <= 0:

        return {
            "success": False,
            "message": (
                "Calorie budget must be greater than zero."
            ),
        }

    memory_store.set_budget(
        session_id=session_id,
        budget=budget,
    )

    consumed = memory_store.total_calories(
        session_id
    )

    remaining = memory_store.remaining_calories(
        session_id
    )

    return {
        "success": True,
        "budget": budget,
        "consumed": consumed,
        "remaining": remaining,
    }