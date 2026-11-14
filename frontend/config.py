"""Settings shared by the whole frontend."""

import os
import sys
from pathlib import Path

# FastAPI backend root. /health is at the root, data lives under /api/v1.
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_V1 = f"{API_URL}/api/v1"

# True forces simulated data. Even when false, the frontend falls back to mock
# data on its own if the backend does not answer or its database is empty.
USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"

# How often data is reloaded (seconds)
REFRESH_SECONDS = 30

# Solar window: the hours we try to move flexible consumption into
SOLAR_WINDOW = (11, 15)

# Prices (lei/kWh) for every savings estimate. They come from the ML pipeline
# (ml_pipeline/ml/tariffs.py), so the questionnaire, the recommendations and the
# ML results all use the same tariff. The fallback values match that file.
_ML_DIR = Path(__file__).resolve().parent.parent / "ml_pipeline"
try:
    if str(_ML_DIR) not in sys.path:
        sys.path.append(str(_ML_DIR))
    from ml.tariffs import FEED_IN_LEI_KWH, RETAIL_LEI_KWH
except Exception:  # ml_pipeline missing or its dependencies not installed
    RETAIL_LEI_KWH, FEED_IN_LEI_KWH = 1.30, 0.30

PRICE_BUY_LEI_KWH = RETAIL_LEI_KWH    # what a kWh from the grid costs the customer
PRICE_SELL_LEI_KWH = FEED_IN_LEI_KWH  # what an exported kWh is worth to the prosumer

# Fixed colours, so charts look the same everywhere. A warm, friendly palette:
# sun is gold, home is light blue, battery is green, grid is lavender.
COLORS = {
    "solar": "#F5A524",
    "consumption": "#4C8DF6",
    "battery": "#22A96B",
    "grid": "#9B7BEA",
    "solar_window": "rgba(245, 165, 36, 0.13)",
    "peak": "#FF7A6B",
    "bar": "#3CC2A6",
    "expected": "#A3AEBB",
}

# Interface colours (backgrounds, text, cards), used by components/theme.py
UI = {
    "bg": "#FBF8F2",
    "card": "#FFFFFF",
    "sidebar": "#EEF6F0",
    "text": "#24323F",
    "muted": "#6B7785",
    "border": "#ECE6DA",
    "grid": "#EFEBE3",
    "primary": "#22A96B",
    "primary_dark": "#17804F",
    "primary_shadow": "rgba(34, 169, 107, 0.28)",
    "hero_from": "#FFF1D2",
    "hero_to": "#E2F5EA",
    "pill_bg": "#E3F5EB",
    "plan_bg": "#EAF7EF",
}

SEVERITY_ORDER = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
