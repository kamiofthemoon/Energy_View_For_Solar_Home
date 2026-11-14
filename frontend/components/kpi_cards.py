"""The big-number cards at the top of the pages."""

import pandas as pd
import streamlit as st

from components.theme import kpi_row


def site_kpis(telemetry: pd.DataFrame, hourly: pd.DataFrame) -> None:
    """A site's KPIs, from telemetry and the hourly profile."""
    now_kw = telemetry["consumption_kw"].iloc[-1]
    today = telemetry[telemetry["timestamp"].dt.date == telemetry["timestamp"].iloc[-1].date()]
    today_kwh = today["energy_kwh"].sum()
    peak = hourly.loc[hourly["avg_power_kw"].idxmax()]
    night = hourly[hourly["hour"].between(2, 5)]["avg_power_kw"].mean()

    kpi_row([
        {"label": "Using now", "value": f"{now_kw:.2f}", "unit": "kW", "color": "consumption"},
        {"label": "Today", "value": f"{today_kwh:.1f}", "unit": "kWh", "color": "bar"},
        {"label": "Peak hour", "value": f"{int(peak['hour'])}:00",
         "sub": f"{peak['avg_power_kw']:.1f} kW on average", "color": "peak"},
        {"label": "Night-time use", "value": f"{night:.2f}", "unit": "kW",
         "sub": "between 02:00 and 05:00", "color": "grid"},
    ])


def fleet_kpis(sites: pd.DataFrame, alerts: pd.DataFrame) -> None:
    """Fleet-wide KPIs, on the O&M page."""
    critical = int((alerts["severity"] == "CRITICAL").sum()) if not alerts.empty else 0
    loss = alerts["estimated_loss_kwh"].sum() if not alerts.empty else 0.0
    under_sla = int((sites["sla_availability_pct"] < 96).sum())

    kpi_row([
        {"label": "Sites", "value": len(sites), "color": "consumption"},
        {"label": "Critical alerts", "value": critical, "color": "peak"},
        {"label": "Estimated losses", "value": f"{loss:.0f}", "unit": "kWh", "color": "solar"},
        {"label": "Below 96% SLA", "value": under_sla, "color": "grid"},
    ])
