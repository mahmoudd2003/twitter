import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BASELINE_PATH = DATA_DIR / "baseline.json"
BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_baseline():
    if BASELINE_PATH.exists():
        try:
            return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_baseline(data: dict):
    BASELINE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_env(name, default=None):
    val = os.getenv(name)
    return val if (val is not None and val != "") else default
