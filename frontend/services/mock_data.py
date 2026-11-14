"""Simulated data, in EXACTLY the same format as the API responses
(see backend/app/routes.py). The frontend falls back to it on its own when
the backend does not answer or has no data, so the demo always works.
"""

from datetime import datetime, timedelta

import numpy as np

SITES = [
    {
        "site_id": "SITE-01",
        "name": "Popescu home",
        "status": "OK",
        "sla_availability_pct": 98.5,
        "total_current_power_kw": 4.1,
        "total_expected_power_kw": 4.3,
        "inverters": [
            {"inverter_id": "INV-01", "name": "Main inverter", "brand": "Huawei",
             "status": "OK", "current_power_kw": 4.1, "expected_power_kw": 4.3,
             "battery_soc_pct": 64.0, "gsm_signal_dbm": -71},
        ],
    },
    {
        "site_id": "SITE-02",
        "name": "Dana's bakery",
        "status": "CRITICAL",
        "sla_availability_pct": 91.2,
        "total_current_power_kw": 9.8,
        "total_expected_power_kw": 14.5,
        "inverters": [
            {"inverter_id": "INV-02", "name": "Workshop inverter", "brand": "Fronius",
             "status": "CRITICAL", "current_power_kw": 9.8, "expected_power_kw": 14.5,
             "battery_soc_pct": None, "gsm_signal_dbm": -89},
        ],
    },
]

ALERTS = [
    {"alert_id": "AL-001", "site_id": "SITE-02", "inverter_id": "INV-02",
     "severity": "CRITICAL", "message": "Production 32% below expected for 6 hours",
     "estimated_loss_kwh": 28.4, "resolved": 0},
    {"alert_id": "AL-002", "site_id": "SITE-01", "inverter_id": "INV-01",
     "severity": "INFO", "message": "30 min of data missing (GSM link)",
     "estimated_loss_kwh": 0.0, "resolved": 0},
]


def _consumption_kw(ts: datetime, site_id: str, rng: np.random.Generator) -> float:
    """Consumption profile: a home with an electric car vs. a bakery."""
    h = ts.hour + ts.minute / 60
    if site_id == "SITE-02":  # bakery: ovens from 3 to 11
        kw = 2.0 + (12.0 if 3 <= h < 11 else 0) + (3.0 if 11 <= h < 18 else 0)
    else:  # home: base load + evening peak + car charging at night
        kw = 0.35
        kw += 2.5 * np.exp(-((h - 19.5) ** 2) / 2)          # cooking, evening lights
        kw += 1.0 * np.exp(-((h - 7.5) ** 2) / 1)           # morning
        if h >= 23 or h < 2:                                 # EV: flat 7 kW block
            kw += 7.0
    return max(0.05, kw + rng.normal(0, 0.08))


def get_telemetry(site_id: str, limit: int = 96) -> list[dict]:
    rng = np.random.default_rng(sum(map(ord, site_id)))
    end = datetime.now().replace(second=0, microsecond=0)
    end -= timedelta(minutes=end.minute % 15)
    out = []
    for k in range(limit):
        ts = end - timedelta(minutes=15 * (limit - 1 - k))
        kw = _consumption_kw(ts, site_id, rng)
        out.append({"timestamp": ts.isoformat(),
                    "consumption_kw": round(kw, 2),
                    "energy_kwh": round(kw * 0.25, 3)})
    return out


def get_hourly_profile(site_id: str) -> list[dict]:
    """7-day average, in the same format as /hourly-profile."""
    rows = get_telemetry(site_id, limit=7 * 96)
    sums, counts = {}, {}
    for r in rows:
        h = datetime.fromisoformat(r["timestamp"]).hour
        sums[h] = sums.get(h, 0) + r["consumption_kw"]
        counts[h] = counts.get(h, 0) + 1
    return [{"hour": h, "avg_power_mw": round(sums[h] / counts[h] / 1000, 4),
             "avg_power_kw": round(sums[h] / counts[h], 2)}
            for h in sorted(sums)]


def get_monthly_summary(site_id: str) -> list[dict]:
    """One year of history, heavier in winter (as in the real PPC curve)."""
    season = {1: 1.9, 2: 2.0, 3: 1.4, 4: 1.0, 5: 0.9, 6: 0.85,
              7: 0.9, 8: 0.9, 9: 0.95, 10: 1.0, 11: 1.4, 12: 1.9}
    base_mwh = 0.45 if site_id == "SITE-01" else 4.0
    today = datetime.now()
    out = []
    for i in range(11, -1, -1):
        m = (today.month - 1 - i) % 12 + 1
        y = today.year - (1 if today.month - i <= 0 else 0)
        out.append({"month": f"{y}-{m:02d}", "total_mwh": round(base_mwh * season[m], 3)})
    return out


def get_sites() -> list[dict]:
    return SITES


def get_alerts() -> list[dict]:
    return ALERTS


def get_ai_context(site_id: str) -> dict:
    """Same format as /sites/{id}/ai-context in the backend."""
    site = next((s for s in SITES if s["site_id"] == site_id), SITES[0])
    hourly = get_hourly_profile(site_id)
    monthly = get_monthly_summary(site_id)
    top = sorted(hourly, key=lambda x: x["avg_power_kw"], reverse=True)[:3]
    day = [h for h in hourly if 9 <= h["hour"] <= 16]
    low = sorted(day, key=lambda x: x["avg_power_kw"])[:3]
    night = [h["avg_power_kw"] for h in hourly if 2 <= h["hour"] <= 5]
    night_kw = round(sum(night) / len(night), 2)
    return {
        "site_id": site_id,
        "site_name": site["name"],
        "inverters": site["inverters"],
        "total_period_consumption_mwh": round(sum(m["total_mwh"] for m in monthly), 2),
        "night_baseload_kw": night_kw,
        "top_peak_hours_to_reduce": top,
        "lowest_consumption_hours_for_load_shifting": low,
        "highest_consumption_month": max(monthly, key=lambda x: x["total_mwh"]),
        "lowest_consumption_month": min(monthly, key=lambda x: x["total_mwh"]),
        "active_alerts": [a["message"] for a in ALERTS if a["site_id"] == site_id],
        "actionable_suggestions": [
            f"Night-time consumption (02:00-05:00) averages {night_kw} kW; check what stays on.",
            f"Consumption peaks at {top[0]['hour']}:00; flexible loads could move to {low[0]['hour']}:00.",
        ],
    }
