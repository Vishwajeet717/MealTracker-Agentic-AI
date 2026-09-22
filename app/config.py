import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
).strip()

try:
    MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "8").strip())
except ValueError:
    MAX_AGENT_STEPS = 8

APP_NAME = "Meal Calorie Helper"


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. "
        "Add it to E:\\Projects\\MealTracker\\.env"
    )