import os
import sys
from pathlib import Path

# Make sure `import app...` resolves to the project root regardless of
# where pytest is invoked from.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Never require a real key for standard test runs.
os.environ.setdefault("GROQ_API_KEY", "test-key-not-real")
