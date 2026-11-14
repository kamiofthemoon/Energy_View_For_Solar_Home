"""Onboarding questionnaire (max 5 steps, everything is a tap, anything can be skipped).

Answers live in st.session_state["profile"]. Right after the last step a first
estimate is shown, so the user sees what the questions were for.
"""

import streamlit as st

from config import PRICE_BUY_LEI_KWH, PRICE_SELL_LEI_KWH

APPLIANCES = {
    "ev": "Electric car",
    "heatpump": "Heat pump / AC",
    "boiler": "Electric water heater",
    "washer": "Washing machine",
    "dishwasher": "Dishwasher",
    "dryer": "Tumble dryer",
    "oven": "Electric hob / oven",
}

# The time-of-use question only makes sense for loads that can actually be moved
SHIFTABLE = ["ev", "boiler", "washer", "dishwasher", "dryer"]

INTERVALS = ["Morning", "Midday", "Evening", "Night", "It varies"]
SCHEDULE = ["Usually home during the day", "Away during the day", "Irregular schedule"]
ENGAGEMENT = [
    "Just a monthly summary",
    "Weekly tips",
    "Notifications at the right moment",
    "Automatic, with connected devices",
]

TOTAL_STEPS = 5


def _profile() -> dict:
    return st.session_state.setdefault("profile", {"step": 1})


def wizard_done() -> bool:
    return st.session_state.get("profile", {}).get("done", False)


def reset_wizard() -> None:
    st.session_state["profile"] = {"step": 1}


def _nav(back: bool = True) -> None:
    p = _profile()
    left, right = st.columns(2)
    if back and p["step"] > 1 and left.button("Back", width="stretch"):
        p["step"] -= 1
        st.rerun()
    label = "Continue" if p["step"] < TOTAL_STEPS else "Done"
    if right.button(label, type="primary", width="stretch"):
        if p["step"] < TOTAL_STEPS:
            p["step"] += 1
        else:
            p["done"] = True
        st.rerun()


def run_wizard() -> None:
    p = _profile()
    st.progress(p["step"] / TOTAL_STEPS, text=f"Step {p['step']} of {TOTAL_STEPS}")

    if p["step"] == 1:
        st.subheader("What do you have installed?")
        st.caption("So we know what energy you produce and what we can optimise. "
                   "PPC already has the technical details, you just confirm.")
        p["equipment"] = st.pills("Pick everything you have:",
                                  ["Solar panels", "Battery", "Electric car",
                                   "Charging station (wallbox)", "Heat pump",
                                   "Electric water heater", "Smart meter", "Smart plugs"],
                                  selection_mode="multi", default=p.get("equipment"))

    elif p["step"] == 2:
        st.subheader("What are the big consumers in your home?")
        st.caption("So we can tell you when they are cheapest to run.")
        labels = list(APPLIANCES.values())
        default = [APPLIANCES[k] for k in p.get("appliances", []) if k in APPLIANCES]
        chosen = st.pills("Pick everything that applies:", labels,
                          selection_mode="multi", default=default or None)
        p["appliances"] = [k for k, v in APPLIANCES.items() if v in (chosen or [])]

    elif p["step"] == 3:
        shiftable = [a for a in p.get("appliances", []) if a in SHIFTABLE]
        st.subheader("When do you usually use them?")
        st.caption("A rough answer is enough. You can skip anything.")
        if not shiftable:
            st.write("You did not pick any appliances that can be scheduled. Just continue.")
        usage = p.setdefault("usage", {})
        for a in shiftable:
            usage[a] = st.segmented_control(APPLIANCES[a], INTERVALS, default=usage.get(a), key=f"use_{a}")
        if "ev" in shiftable:
            st.divider()
            p["ev_km"] = st.select_slider("Roughly how many km do you drive a day?",
                                          ["under 20", "20-50", "50-100", "over 100", "Not sure"],
                                          value=p.get("ev_km", "20-50"))
            p["ev_home_noon"] = st.segmented_control("Is the car at home around midday?",
                                                     ["Usually yes", "Only at weekends", "Rarely"],
                                                     default=p.get("ev_home_noon"))

    elif p["step"] == 4:
        st.subheader("What does a typical day look like for you?")
        st.caption("So we don't suggest things for when you are not home.")
        p["schedule"] = st.segmented_control("Your schedule:", SCHEDULE, default=p.get("schedule"))

    elif p["step"] == 5:
        st.subheader("How involved do you want to be?")
        st.caption("You can change this any time in the settings.")
        p["engagement"] = st.radio("Choose a level:", ENGAGEMENT,
                                   index=ENGAGEMENT.index(p["engagement"]) if p.get("engagement") in ENGAGEMENT else 2)
        st.divider()
        st.caption("Separate from how involved you are: which data you share with us. "
                   "The app works without it, the estimates are just less precise.")
        p["data_meter"] = st.toggle("Load curve from the smart meter",
                                    value=p.get("data_meter", True))
        p["data_devices"] = st.toggle("Connected devices (smart plugs, charger)",
                                      value=p.get("data_devices", False))

    _nav()


def first_estimate() -> None:
    """The first result, shown right after the questionnaire."""
    p = st.session_state.get("profile", {})
    saving = 0.0
    parts = []
    if "ev" in p.get("appliances", []):
        # ~10 kWh/day of charging moved from the night into the solar window, 20 days a month
        ev_saving = 10 * 20 * (PRICE_BUY_LEI_KWH - PRICE_SELL_LEI_KWH)
        saving += ev_saving
        parts.append(f"charging the car in the sunny hours (~{ev_saving:.0f} lei/month)")
    for a in ("boiler", "washer", "dishwasher", "dryer"):
        if a in p.get("appliances", []):
            saving += 15
            parts.append(APPLIANCES[a].lower() + " moved to midday (~15 lei/month)")
    if not parts:
        st.info("Profile saved. Recommendations will appear as we collect data about your consumption.")
        return
    st.success(f"Based on your profile, you could save about **{saving:.0f} lei/month**: "
               + "; ".join(parts) + ". A rough estimate, refined as real data comes in.")
