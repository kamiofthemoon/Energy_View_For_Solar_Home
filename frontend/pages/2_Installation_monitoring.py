"""Installation monitoring (PPC's operations and maintenance team): every site,
its alerts and what each problem costs - the answer to "faults found after the
damage"."""

import streamlit as st

from components.charts import inverter_power_chart, pv_vs_expected_chart
from components.kpi_cards import fleet_kpis
from components.theme import hero, kpi_row, setup_page
from config import SEVERITY_ORDER
from services import api_client, ml_source

setup_page("Installation monitoring")

hero("Installation monitoring",
     "Every installation and its problems in one place - for the operations and maintenance team",
     eyebrow="Operations & maintenance")
api_client.api_status_banner()

# --- ML pipeline version: alerts with the loss in lei ------------------------
if ml_source.available():
    sites = ml_source.get_sites()
    alerts = ml_source.get_alerts()
    active = alerts[alerts["ongoing"].astype(bool)]

    kpi_row([
        {"label": "Installations", "value": len(sites), "color": "consumption"},
        {"label": "Active alerts", "value": len(active), "color": "solar"},
        {"label": "Lei at stake", "value": f"{active['lost_lei'].sum():.0f}", "unit": "lei",
         "sub": "from the active alerts", "color": "grid"},
        {"label": "Critical", "value": int((alerts["severity"] == "critical").sum()), "color": "peak"},
    ])

    st.subheader("Alerts, most expensive first")
    show = alerts.sort_values("lost_lei", ascending=False)
    st.dataframe(
        show[["site_name", "type", "severity", "detected_at", "ongoing",
              "lost_kwh", "lost_lei", "action"]],
        column_config={
            "site_name": "Installation", "type": "Type", "severity": "Severity",
            "detected_at": st.column_config.DatetimeColumn("Detected", format="DD.MM HH:mm"),
            "ongoing": "Active",
            "lost_kwh": st.column_config.NumberColumn("Lost (kWh)", format="%.0f"),
            "lost_lei": st.column_config.NumberColumn("Lost (lei)", format="%.0f"),
            "action": "Recommended action",
        },
        hide_index=True, width="stretch",
    )

    st.subheader("One installation's production: expected vs. actual")
    options = dict(zip(sites["name"], sites["site_id"]))
    name = st.selectbox("Installation", list(options))
    ts = ml_source.get_timeseries(options[name], days=7)
    st.caption("The last 7 days. A dip below the grey line means a fault "
               "or missing data.")
    st.plotly_chart(pv_vs_expected_chart(ts), width="stretch", theme=None)
    st.stop()

# --- Backend / mock version --------------------------------------------------
sites = api_client.get_sites()
alerts = api_client.get_alerts()

fleet_kpis(sites, alerts)

st.subheader("Active alerts")
if alerts.empty:
    st.success("No active alerts.")
else:
    df = alerts.merge(sites[["site_id", "name"]], on="site_id", how="left")
    df["_ord"] = df["severity"].map(SEVERITY_ORDER).fillna(9)
    df = df.sort_values(["_ord", "estimated_loss_kwh"], ascending=[True, False])
    st.dataframe(
        df[["severity", "name", "message", "estimated_loss_kwh"]],
        column_config={
            "severity": "Severity",
            "name": "Site",
            "message": "Problem",
            "estimated_loss_kwh": st.column_config.NumberColumn("Estimated loss (kWh)",
                                                                format="%.1f"),
        },
        hide_index=True, width="stretch",
    )

st.subheader("Sites")
view = sites.copy()
view["delta_kw"] = (view["total_current_power_kw"] - view["total_expected_power_kw"]).round(2)
st.dataframe(
    view[["site_id", "name", "status", "sla_availability_pct",
          "total_current_power_kw", "total_expected_power_kw", "delta_kw"]],
    column_config={
        "site_id": "ID", "name": "Name", "status": "Status",
        "sla_availability_pct": st.column_config.NumberColumn("SLA (%)", format="%.1f"),
        "total_current_power_kw": "Now (kW)",
        "total_expected_power_kw": "Expected (kW)",
        "delta_kw": "Difference (kW)",
    },
    hide_index=True, width="stretch",
)

st.subheader("Inverters of one site")
options = dict(zip(sites["name"], sites["site_id"]))
name = st.selectbox("Site", list(options))
inverters = api_client.get_inverters(options[name])
if inverters.empty:
    st.info("This site has no registered inverters.")
else:
    left, right = st.columns([2, 3])
    with left:
        st.dataframe(
            inverters[["name", "brand", "status", "battery_soc_pct", "gsm_signal_dbm"]],
            column_config={
                "name": "Inverter", "brand": "Brand", "status": "Status",
                "battery_soc_pct": st.column_config.NumberColumn("Battery (%)", format="%.0f"),
                "gsm_signal_dbm": "GSM signal (dBm)",
            },
            hide_index=True, width="stretch",
        )
    with right:
        st.plotly_chart(inverter_power_chart(inverters), width="stretch", theme=None)

with st.expander("Context sent to the AI service (ai-context)"):
    st.json(api_client.get_ai_context(options[name]))
