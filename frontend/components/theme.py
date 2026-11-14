"""The app's shared look: theme, font, cards and the chart template.

Every page calls setup_page() instead of st.set_page_config(), so they all
look the same. Colours come from config.COLORS / config.UI.
"""

import html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from config import COLORS, UI

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, textarea, select {{
    font-family: 'Nunito', system-ui, -apple-system, 'Segoe UI', sans-serif !important;
}}
.stApp {{ background: {UI['bg']}; }}
header[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer, [data-testid="stAppDeployButton"] {{ visibility: hidden; }}
/* The main page shows up in the menu as "app" (its file name): rename it */
[data-testid="stSidebarNav"] span[label="app"] p {{ font-size: 0; }}
[data-testid="stSidebarNav"] span[label="app"] p::after {{ content: "Home"; font-size: .95rem; }}
.block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1240px; }}

h1, h2, h3 {{ color: {UI['text']}; font-weight: 800 !important; letter-spacing: -0.01em; }}
h3 {{ font-size: 1.25rem !important; margin-top: 0.6rem; }}
[data-testid="stCaptionContainer"] {{ color: {UI['muted']}; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: {UI['sidebar']}; border-right: 1px solid {UI['border']}; }}
[data-testid="stSidebarNav"] a {{ border-radius: 12px; }}

/* Rounded buttons */
.stButton > button, .stPageLink a {{
    border-radius: 999px !important; font-weight: 700; padding: 0.45rem 1.1rem;
    transition: transform .08s ease, box-shadow .15s ease;
}}
.stButton > button:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(36,50,63,.10); }}
.stButton > button[kind="primary"] {{ box-shadow: 0 4px 14px {UI['primary_shadow']}; }}

/* Bordered containers = white cards */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]),
div[data-testid="stVerticalBlock"][class*="border"] {{
    background: {UI['card']}; border-color: {UI['border']} !important; border-radius: 18px;
    box-shadow: 0 2px 10px rgba(36,50,63,.05);
}}

/* Any remaining st.metric: also a card */
[data-testid="stMetric"] {{
    background: {UI['card']}; border: 1px solid {UI['border']}; border-radius: 18px;
    padding: 14px 18px; box-shadow: 0 2px 10px rgba(36,50,63,.05);
}}
[data-testid="stMetricValue"] {{ font-weight: 800; color: {UI['text']}; }}

/* Charts and tables on a white background */
[data-testid="stPlotlyChart"] {{
    background: {UI['card']}; border: 1px solid {UI['border']}; border-radius: 18px;
    padding: 8px; box-shadow: 0 2px 10px rgba(36,50,63,.05); box-sizing: border-box;
}}
[data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; box-shadow: 0 2px 10px rgba(36,50,63,.05); }}
[data-testid="stExpander"] details {{ background: {UI['card']}; border-radius: 14px; border-color: {UI['border']}; }}
[data-testid="stAlert"] {{ border-radius: 14px; }}

/* Hero */
.ev-hero {{
    background: linear-gradient(120deg, {UI['hero_from']} 0%, {UI['hero_to']} 100%);
    border-radius: 24px; padding: 26px 30px; margin-bottom: 18px;
    border: 1px solid {UI['border']};
}}
.ev-eyebrow {{ font-size: .78rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase;
               color: {UI['primary_dark']}; margin-bottom: 6px; }}
.ev-hero-title {{ font-size: 2rem; font-weight: 800; color: {UI['text']}; line-height: 1.15; }}
.ev-hero-sub {{ font-size: 1.02rem; color: {UI['muted']}; margin-top: 6px; max-width: 720px; }}

/* KPI cards */
.ev-kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 14px; margin: 4px 0 18px; }}
.ev-kpi {{
    background: {UI['card']}; border: 1px solid {UI['border']}; border-radius: 18px;
    padding: 16px 18px; box-shadow: 0 2px 10px rgba(36,50,63,.05);
    border-top: 5px solid var(--accent);
}}
.ev-kpi-label {{ display: flex; align-items: center; gap: 8px; font-size: .9rem; font-weight: 700;
                 color: {UI['muted']}; }}
.ev-kpi-dot {{ width: 10px; height: 10px; border-radius: 50%; background: var(--accent); }}
.ev-kpi-value {{ font-size: 1.85rem; font-weight: 800; color: {UI['text']}; margin-top: 4px; }}
.ev-kpi-value small {{ font-size: 1rem; font-weight: 700; color: {UI['muted']}; margin-left: 2px; }}
.ev-kpi-sub {{ font-size: .85rem; color: {UI['muted']}; margin-top: 2px; }}

/* Recommendations */
.ev-rec-title {{ font-size: 1.08rem; font-weight: 800; color: {UI['text']}; }}
.ev-rec-body {{ color: {UI['text']}; opacity: .85; margin: 6px 0 10px; }}
.ev-pill {{ display: inline-block; padding: 4px 12px; border-radius: 999px; font-weight: 700;
            font-size: .85rem; background: {UI['pill_bg']}; color: {UI['primary_dark']}; }}

/* Accepted plan */
.ev-plan {{ background: {UI['plan_bg']}; border-radius: 18px; padding: 18px 20px; margin-bottom: 14px;
            border: 1px solid {UI['border']}; }}
.ev-plan-big {{ font-size: 1.9rem; font-weight: 800; color: {UI['primary_dark']}; }}
.ev-plan ul {{ margin: 8px 0 0 0; padding-left: 1.1rem; color: {UI['text']}; }}
</style>
"""


def _register_plotly_template() -> None:
    tpl = go.layout.Template(pio.templates["plotly_white"])
    tpl.layout.update(
        font=dict(family="Nunito, system-ui, sans-serif", size=13, color=UI["text"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[COLORS["solar"], COLORS["consumption"], COLORS["battery"], COLORS["grid"],
                  COLORS["bar"], COLORS["peak"]],
        xaxis=dict(gridcolor=UI["grid"], zeroline=False, linecolor=UI["border"]),
        yaxis=dict(gridcolor=UI["grid"], zeroline=False, linecolor=UI["border"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="white", bordercolor=UI["border"],
                        font=dict(family="Nunito, sans-serif", color=UI["text"])),
        bargap=0.25,
    )
    pio.templates["energy_friendly"] = tpl
    pio.templates.default = "energy_friendly"


def setup_page(title: str) -> None:
    """Configures the page and applies the theme. Must be the first Streamlit call on a page."""
    st.set_page_config(page_title=f"{title} | One Energy View", layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)
    _register_plotly_template()


def hero(title: str, subtitle: str = "", eyebrow: str = "One Energy View") -> None:
    st.markdown(
        f'<div class="ev-hero"><div class="ev-eyebrow">{html.escape(eyebrow)}</div>'
        f'<div class="ev-hero-title">{html.escape(title)}</div>'
        + (f'<div class="ev-hero-sub">{html.escape(subtitle)}</div>' if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def kpi_row(items: list[dict]) -> None:
    """A row of cards. Each item: label, value, unit (opt.), sub (opt.), color (COLORS key or hex)."""
    cards = []
    for it in items:
        color = COLORS.get(it.get("color", ""), it.get("color", UI["primary"]))
        unit = f"<small>{html.escape(str(it['unit']))}</small>" if it.get("unit") else ""
        sub = f'<div class="ev-kpi-sub">{html.escape(str(it["sub"]))}</div>' if it.get("sub") else ""
        cards.append(
            f'<div class="ev-kpi" style="--accent:{color}">'
            f'<div class="ev-kpi-label"><span class="ev-kpi-dot"></span>{html.escape(it["label"])}</div>'
            f'<div class="ev-kpi-value">{html.escape(str(it["value"]))}{unit}</div>{sub}</div>'
        )
    st.markdown(f'<div class="ev-kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
