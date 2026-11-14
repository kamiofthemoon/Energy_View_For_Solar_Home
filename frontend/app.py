"""Main page: the customer's (prosumer's) screen.

The first time it runs the onboarding questionnaire; after that it shows the
current state, the recommendations and the accepted plan. If the ML pipeline
results exist (ml_pipeline/out/), the screen uses the full picture: solar +
home + battery + grid and the personalised recommendations. Otherwise it falls
back to the backend / mock data.

Run: streamlit run app.py
"""

import streamlit as st

from components.charts import one_view_chart
from components.kpi_cards import site_kpis
from components.notifications import accepted_plan, build_notifications, notification_inbox
from components.theme import hero, kpi_row, setup_page
from components.wizard import first_estimate, reset_wizard, run_wizard, wizard_done
from services import api_client, ml_source

setup_page("Home")

api_client.api_status_banner()

# --- Onboarding questionnaire, until it is completed -------------------------
if not wizard_done():
    hero("Welcome!",
         "A few short questions so the tips fit your home. You can skip any of them.")
    run_wizard()
    st.stop()

use_ml = ml_source.available()

# --- Choosing the installation -----------------------------------------------
sites = ml_source.get_sites() if use_ml else api_client.get_sites()
if sites.empty:
    st.error("No sites found. Start the backend, run the seed script or "
             "generate the ML data with `python run_demo.py`.")
    st.stop()

with st.sidebar:
    options = dict(zip(sites["name"], sites["site_id"]))
    name = st.selectbox("My installation", list(options))
    site_id = options[name]
    if st.button("Redo the questionnaire"):
        reset_wizard()
        st.rerun()

hero(f"Hi! Here is how {name} is doing",
     "Everything you produce, use and store in one place, plus what you can do today to pay less.")
first_estimate()
profile = st.session_state.get("profile", {})

if use_ml:
    # --- ML pipeline version: the full energy picture ------------------------
    ts = ml_source.get_timeseries(site_id, days=3)
    last = ts.iloc[-1]
    no_batt = last.isna()["battery_soc"]
    kpi_row([
        {"label": "Solar now", "value": f"{last['pv_kw']:.1f}", "unit": "kW", "color": "solar",
         "sub": "from your panels"},
        {"label": "Home uses", "value": f"{last['load_kw']:.1f}", "unit": "kW",
         "color": "consumption", "sub": "right now"},
        {"label": "Battery", "value": "none" if no_batt else f"{last['battery_soc']:.0f}",
         "unit": "" if no_batt else "%", "color": "battery",
         "sub": "no battery registered" if no_batt else "state of charge"},
        {"label": "Grid", "value": f"{abs(last['grid_kw']):.1f}", "unit": "kW", "color": "grid",
         "sub": "buying from the grid" if last["grid_kw"] > 0 else "selling to the grid"},
    ])

    st.subheader("Produced, used and stored - last 3 days")
    st.plotly_chart(one_view_chart(ts), width="stretch", theme=None)

left, right = st.columns([3, 2])

with left:
    st.subheader("Recommendations for you")
    st.caption("Only a few, and only when they are worth it. Each one takes a single tap.")
    if use_ml:
        hourly = ml_source.get_hourly_profile(site_id)
        cards = ml_source.nudges_as_notifications(site_id)
        # local rules (from the questionnaire) fill in what the ML does not cover
        ml_ids = {c["id"] for c in cards}
        cards += [c for c in build_notifications(hourly, profile) if c["id"] not in ml_ids]
        notification_inbox(cards)

        info = ml_source.get_customer(site_id)
        bench = info.get("benchmark", {})
        if bench.get("flag") and bench.get("text"):
            st.warning(bench["text"])
        if info.get("tips"):
            with st.expander("Good time windows in the next few days"):
                for tip in info["tips"]:
                    st.markdown(f"- {tip}")
    else:
        hourly = api_client.get_hourly_profile(site_id)
        notification_inbox(build_notifications(hourly, profile))
        ai_recs = api_client.get_ai_recommendations(site_id)
        if ai_recs:
            with st.expander("Recommendations from the AI service"):
                for r in ai_recs:
                    st.markdown(f"- {r}")

with right:
    accepted_plan()
    if use_ml:
        info = ml_source.get_customer(site_id)
        if info.get("dispatch_texts"):
            st.subheader("Your battery, tomorrow")
            st.caption(f"Gain compared with 'always export': "
                       f"~{info.get('dispatch_uplift_lei', 0):.1f} lei/day")
            for line in info["dispatch_texts"]:
                st.markdown(f"- {line}")
    else:
        telemetry = api_client.get_telemetry(site_id, limit=96)
        site_kpis(telemetry, api_client.get_hourly_profile(site_id))
    st.subheader("Want to see why?")
    st.page_link("pages/1_Consumption_analysis.py", label="Your consumption, by hour and by day")
