"""Consumption analysis for one site: the 15-minute curve, the hourly profile and
the history. This is where you see WHY the customer gets the recommendations they get."""

import streamlit as st

from components.charts import (consumption_chart, daily_energy_chart, hourly_profile_chart,
                               monthly_chart, pv_vs_expected_chart)
from components.kpi_cards import site_kpis
from components.theme import hero, setup_page
from config import SOLAR_WINDOW
from services import api_client, ml_source

setup_page("Consumption analysis")

use_ml = ml_source.available()
api_client.api_status_banner()

sites = ml_source.get_sites() if use_ml else api_client.get_sites()
if sites.empty:
    st.error("No sites found. Start the backend or run the seed script.")
    st.stop()

options = dict(zip(sites["name"], sites["site_id"]))
col1, col2 = st.columns([3, 1])
name = col1.selectbox("Installation", list(options))
days = col2.selectbox("Range", [1, 2, 3, 7],
                      format_func=lambda d: "Last day" if d == 1 else f"Last {d} days")
site_id = options[name]

if use_ml:
    telemetry = ml_source.get_timeseries(site_id, days=days)
    hourly = ml_source.get_hourly_profile(site_id)
else:
    telemetry = api_client.get_telemetry(site_id, limit=days * 96)
    hourly = api_client.get_hourly_profile(site_id)

hero(name, "Where the recommendations come from: your consumption by hour, by day and against the sun.",
     eyebrow="Consumption analysis")
site_kpis(telemetry, hourly)

st.subheader("Consumption every 15 minutes")
st.caption(f"The yellow background is the solar window ({SOLAR_WINDOW[0]}:00-{SOLAR_WINDOW[1]}:00): "
           "that is where we want to move flexible consumption.")
st.plotly_chart(consumption_chart(telemetry), width="stretch", theme=None)

if use_ml:
    st.subheader("Production: expected from the weather vs. actual")
    st.caption("When the actual line drops below the expected one, something is wrong - "
               "this is what triggers the monitoring team's alerts.")
    st.plotly_chart(pv_vs_expected_chart(telemetry), width="stretch", theme=None)

left, right = st.columns(2)
with left:
    st.subheader("Average hourly profile")
    peaks = hourly.nlargest(3, "avg_power_kw")["hour"].tolist()
    st.caption("Coral = the 3 peak hours. Yellow = the solar window.")
    st.plotly_chart(hourly_profile_chart(hourly, peaks), width="stretch", theme=None)
with right:
    if use_ml:
        st.subheader("Energy per day")
        st.caption("The last 14 days, from the ML pipeline data.")
        st.plotly_chart(daily_energy_chart(ml_source.get_daily_energy(site_id)), width="stretch", theme=None)
    else:
        st.subheader("Monthly history")
        st.caption("Seasonal consumption, straight from the PPC load curve.")
        st.plotly_chart(monthly_chart(api_client.get_monthly_summary(site_id)), width="stretch", theme=None)
