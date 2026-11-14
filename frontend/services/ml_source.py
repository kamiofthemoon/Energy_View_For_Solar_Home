"""Reads the ML pipeline results (ml_pipeline/out/*.csv), if they exist.

This is the best data source: production + consumption + battery + grid,
weather-expected production, alerts with the loss in lei and personalised
recommendations (customer.json). Generate them with:

    cd ml_pipeline && python run_demo.py
"""

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from config import REFRESH_SECONDS

TZ = "Europe/Bucharest"


def _out_dir() -> Path:
    override = os.getenv("ML_OUT")
    if override:
        return Path(override)
    for p in ("../ml_pipeline/out", "ml_pipeline/out"):
        if Path(p).exists():
            return Path(p)
    return Path("../ml_pipeline/out")


def available() -> bool:
    out = _out_dir()
    return (out / "sites.csv").exists() and (out / "telemetry.csv").exists()


@st.cache_data(ttl=REFRESH_SECONDS)
def get_sites() -> pd.DataFrame:
    return pd.read_csv(_out_dir() / "sites.csv")


@st.cache_data(ttl=REFRESH_SECONDS)
def _telemetry() -> pd.DataFrame:
    out = _out_dir()
    df = pd.read_csv(out / "telemetry.csv", parse_dates=["timestamp"])
    exp = pd.read_csv(out / "expected.csv", parse_dates=["timestamp"])
    df = df.merge(exp[["timestamp", "site_id", "expected_kw"]],
                  on=["timestamp", "site_id"], how="left")
    df["timestamp"] = df["timestamp"].dt.tz_convert(TZ).dt.tz_localize(None)
    return df


def get_timeseries(site_id: str, days: int = 3) -> pd.DataFrame:
    df = _telemetry()
    df = df[df["site_id"] == site_id]
    t0 = df["timestamp"].max() - pd.Timedelta(days=days)
    df = df[df["timestamp"] >= t0].copy()
    # columns compatible with the pages that only know about consumption
    df["consumption_kw"] = df["load_kw"]
    df["energy_kwh"] = df["load_kw"] * 0.25
    return df


def get_hourly_profile(site_id: str) -> pd.DataFrame:
    df = _telemetry()
    df = df[df["site_id"] == site_id]
    g = df.groupby(df["timestamp"].dt.hour)["load_kw"].mean().round(2)
    return pd.DataFrame({"hour": g.index, "avg_power_kw": g.values})


def get_daily_energy(site_id: str, days: int = 14) -> pd.DataFrame:
    df = get_timeseries(site_id, days)
    g = (df.groupby(df["timestamp"].dt.date)["energy_kwh"].sum()).round(1)
    return pd.DataFrame({"day": [d.strftime("%d %b") for d in g.index], "kwh": g.values})


@st.cache_data(ttl=REFRESH_SECONDS)
def get_alerts() -> pd.DataFrame:
    df = pd.read_csv(_out_dir() / "alerts.csv")
    df["detected_at"] = (pd.to_datetime(df["detected_at"], utc=True)
                         .dt.tz_convert(TZ).dt.tz_localize(None))
    return df


@st.cache_data(ttl=REFRESH_SECONDS)
def get_customer(site_id: str) -> dict:
    p = _out_dir() / "customer.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text()).get(site_id, {})


def nudges_as_notifications(site_id: str) -> list[dict]:
    """The ML recommendations, in the inbox card format."""
    info = get_customer(site_id)
    cards = []
    for i, n in enumerate(info.get("nudges", [])):
        cards.append({
            "id": f"ml_nudge_{site_id}_{i}",
            "title": "A habit spotted in your consumption",
            "body": n["text"],
            "saving": float(n.get("saving_lei_per_run", 0)),
        })
    return cards
