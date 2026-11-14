"""The customer's notification inbox (simulated in the prototype).

Design rules: only a few and only when worth it (a minimum saving in lei),
each one solved with a single tap, and "Don't suggest this again" is actually
remembered. Notifications are built from the real hourly profile plus the
questionnaire profile.
"""

import html

import pandas as pd
import streamlit as st

from components.wizard import APPLIANCES
from config import PRICE_BUY_LEI_KWH, PRICE_SELL_LEI_KWH, SOLAR_WINDOW

MIN_SAVING_LEI = 2.0  # below this threshold we don't bother the customer


def build_notifications(hourly: pd.DataFrame, profile: dict) -> list[dict]:
    """Builds the notifications from the data, not from a fixed list."""
    notifs = []
    solar = f"{SOLAR_WINDOW[0]}:00-{SOLAR_WINDOW[1]}:00"
    peak_hour = int(hourly.loc[hourly["avg_power_kw"].idxmax(), "hour"])
    night = hourly[hourly["hour"].between(2, 5)]["avg_power_kw"].mean()
    diff = PRICE_BUY_LEI_KWH - PRICE_SELL_LEI_KWH

    if "ev" in profile.get("appliances", []):
        away = profile.get("ev_home_noon") == "Rarely"
        if away:
            notifs.append({
                "id": "ev_partial",
                "title": "Charge the car tonight only as much as you need",
                "body": "The car is not home at midday, so tonight charge it only to ~60%, "
                        "enough for tomorrow's trips. Top up the rest at the weekend, from the sun.",
                "saving": round(5 * diff, 1),
            })
        else:
            notifs.append({
                "id": "ev_solar",
                "title": f"Charge the car between {solar}",
                "body": "In this window your panels produce the most and energy costs you the least. "
                        "Moving a ~10 kWh charge from the night to midday shows up straight on your bill.",
                "saving": round(10 * diff, 1),
            })
    for a in ("washer", "dishwasher", "boiler", "dryer"):
        if a in profile.get("appliances", []) and profile.get("usage", {}).get(a) in ("Evening", "Night", None):
            notifs.append({
                "id": f"shift_{a}",
                "title": f"{APPLIANCES[a]}: run it at midday",
                "body": f"It usually runs in the evening, when your home is already at its peak "
                        f"(around {peak_hour}:00). Between {solar} it would run on your panels' energy.",
                "saving": round(1.5 * diff, 1),
            })
    if night and night > 0.3:
        notifs.append({
            "id": "baseload",
            "title": "Something keeps running while you sleep",
            "body": f"Between 02:00 and 05:00 your home draws {night:.2f} kW on average. "
                    "Check what stays on overnight (water heater, devices on standby).",
            "saving": round(night * 6 * PRICE_BUY_LEI_KWH, 1),
        })

    notifs = [n for n in notifs if n["saving"] >= MIN_SAVING_LEI / 7 or n["id"] == "baseload"]
    dismissed = st.session_state.setdefault("notif_dismissed", set())
    return [n for n in notifs if n["id"] not in dismissed]


def notification_inbox(notifs: list[dict]) -> None:
    accepted = st.session_state.setdefault("notif_accepted", {})
    dismissed = st.session_state.setdefault("notif_dismissed", set())
    pending = [n for n in notifs if n["id"] not in accepted]

    if not pending:
        st.success("Nothing new. We only get in touch when you really have something to gain.")
    for n in pending:
        with st.container(border=True):
            st.markdown(
                f'<div class="ev-rec-title">{html.escape(n["title"])}</div>'
                f'<div class="ev-rec-body">{html.escape(n["body"])}</div>'
                f'<span class="ev-pill">~{n["saving"]:.0f} lei saved on each day you do it</span>',
                unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            if c1.button("Accept", key=f"acc_{n['id']}", type="primary", width="stretch"):
                accepted[n["id"]] = n
                st.rerun()
            if c2.button("Not today", key=f"later_{n['id']}", width="stretch"):
                st.toast("Fine, we'll come back to it another time.")
            if c3.button("Don't suggest again", key=f"dis_{n['id']}", width="stretch"):
                dismissed.add(n["id"])
                st.rerun()


def accepted_plan() -> None:
    accepted = st.session_state.get("notif_accepted", {})
    if not accepted:
        return
    st.subheader("Your plan")
    total = sum(n["saving"] for n in accepted.values())
    items = "".join(f"<li>{html.escape(n['title'])}</li>" for n in accepted.values())
    st.markdown(
        f'<div class="ev-plan"><div class="ev-kpi-sub">Estimated savings if you stick to it</div>'
        f'<div class="ev-plan-big">~{total * 20:.0f} lei/month</div><ul>{items}</ul></div>',
        unsafe_allow_html=True)
