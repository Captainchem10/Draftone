"""
utils.py — Shared helpers for the Smurfit Westrock ESG Dashboard
Centralises data loading, color maps, label maps, KPI formatters,
and reusable Plotly layout defaults.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
INVENTORY_FILE  = "05022026_SW_Data_Inventory.xlsx"
CARBON_FILE     = "SW_Carbon_Footprint.xlsx"
P2P_FILE        = "SW_P2P_Review.xlsx"

# ─────────────────────────────────────────────
# LABEL & COLOR MAPS
# ─────────────────────────────────────────────
COMPANY_MAP: dict[str, str] = {
    "SW":  "Smurfit Westrock",
    "PKG": "Packaging Corp",
    "IP":  "Intl Paper",
    "GPI": "Graphic Packaging",
    "SK":  "Smurfit Kappa",
    "WK":  "WestRock",
}

COMPANY_COLORS: dict[str, str] = {
    "SW":  "#1e90ff",
    "PKG": "#ff6b35",
    "IP":  "#4caf82",
    "GPI": "#ffd700",
    "SK":  "#c678dd",
    "WK":  "#56b6c2",
}

BIZ_COLORS: dict[str, str] = {
    "S":  "#1e90ff",
    "W":  "#ff6b35",
    "SW": "#4caf82",
}

BIZ_LABELS: dict[str, str] = {
    "S":  "Smurfit Kappa (S)",
    "W":  "WestRock (W)",
    "SW": "Combined (SW)",
}

PILLAR_COLORS: dict[str, str] = {
    "E": "#4caf82",
    "S": "#1e90ff",
    "G": "#ffd700",
    "P": "#ff6b35",
    "F": "#c678dd",
}

PILLAR_LABELS: dict[str, str] = {
    "E": "Environmental",
    "S": "Social",
    "G": "Governance",
    "P": "Performance",
    "F": "Financial",
}

QUALITY_COLORS: dict[str, str] = {
    "✅ High Quality":  "#4caf82",
    "🟡 Acceptable":    "#ffd700",
    "🔴 Poor Quality":  "#e06c75",
    "⬜ Not Scored":    "#8da9c4",
}

# ─────────────────────────────────────────────
# PLOTLY DARK LAYOUT DEFAULTS
# ─────────────────────────────────────────────
DARK_BG   = "#162032"
GRID_CLR  = "#2e4057"
TICK_CLR  = "#8da9c4"
TEXT_CLR  = "#c0d8f0"

def dark_layout(**kwargs) -> dict:
    """Return a base Plotly layout dict styled for the dark theme."""
    base = dict(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT_CLR, family="IBM Plex Mono, monospace"),
        xaxis=dict(
            gridcolor=GRID_CLR,
            linecolor=GRID_CLR,
            tickfont=dict(color=TICK_CLR),
        ),
        yaxis=dict(
            gridcolor=GRID_CLR,
            linecolor=GRID_CLR,
            tickfont=dict(color=TICK_CLR),
        ),
        legend=dict(
            font=dict(color=TEXT_CLR),
            bgcolor=DARK_BG,
            bordercolor=GRID_CLR,
        ),
        margin=dict(l=48, r=24, t=32, b=40),
        hoverlabel=dict(
            bgcolor="#1e2a3a",
            bordercolor=GRID_CLR,
            font=dict(color="#e8f4fd"),
        ),
    )
    base.update(kwargs)
    return base


# ─────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_esg() -> pd.DataFrame:
    """Load and clean the ESG pivot sheet from the Data Inventory workbook."""
    df = pd.read_excel(INVENTORY_FILE, sheet_name="ESG", engine="openpyxl")
    df.columns = [
        "Pillar", "KPI_Category", "KPI_Name",
        "Total_Value", "Business", "Unit",
        "Reporting_Year", "Unit_per_Revenue", "Unit_per_MarketCap",
    ]
    df["Total_Value"]    = pd.to_numeric(df["Total_Value"],    errors="coerce")
    df["Reporting_Year"] = pd.to_numeric(df["Reporting_Year"], errors="coerce")
    df["Unit_per_Revenue"]    = pd.to_numeric(df["Unit_per_Revenue"],    errors="coerce")
    df["Unit_per_MarketCap"]  = pd.to_numeric(df["Unit_per_MarketCap"],  errors="coerce")
    return df.dropna(subset=["Pillar", "KPI_Category"])


@st.cache_data(show_spinner=False)
def load_inventory_scored() -> pd.DataFrame:
    """Load scored rows from E, S, G, P data inventory sheets and concat."""
    frames = []
    sheet_map = {
        "E Data_Inventory": "E",
        "S Data_Inventory ": "S",
        "G Data_Inventory ": "G",
        "P Data_Inventory": "P",
    }
    for sheet, pillar in sheet_map.items():
        try:
            raw = pd.read_excel(INVENTORY_FILE, sheet_name=sheet,
                                header=1, engine="openpyxl")
            raw.columns = raw.columns.str.strip()
            # Standardise column names regardless of emoji / newlines
            raw.columns = [
                str(c)
                .replace("\n", " ")
                .replace("  ", " ")
                .strip()
                for c in raw.columns
            ]
            # Only keep rows that have a KPI Name
            raw = raw.dropna(subset=["KPI Name"])
            raw["_Pillar"] = pillar
            frames.append(raw)
        except Exception:
            pass

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)

    # Numeric columns
    for col in combined.columns:
        if "Score" in col or "Value" in col:
            combined[col] = pd.to_numeric(combined[col], errors="coerce")

    return combined


@st.cache_data(show_spinner=False)
def load_p2p() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load P2P dashboard data and market cap table."""
    raw = pd.read_excel(P2P_FILE, sheet_name="Dashboard", engine="openpyxl")
    p2p = raw[
        ["Company", "Pilar", "Metric", "Weight", "Score", "Disclosure", "Peer Rank"]
    ].dropna(subset=["Company"]).copy()
    p2p["Score"]  = pd.to_numeric(p2p["Score"],  errors="coerce")
    p2p["Weight"] = pd.to_numeric(p2p["Weight"], errors="coerce")

    mktcap = pd.read_excel(P2P_FILE, sheet_name="Market Cap", engine="openpyxl")
    return p2p, mktcap


@st.cache_data(show_spinner=False)
def load_carbon_trend() -> pd.DataFrame:
    """Load the 3-year emissions trend from the Carbon Footprint workbook."""
    return pd.DataFrame({
        "Year":     [2022, 2023, 2024],
        "Scope1":   [0,    0,    38_297_137.68],
        "Scope2_MB":[0,    0,    0],
        "Scope2_LB":[0,    0,    0],
        "Scope3":   [0,    0,    0],
        "Total":    [16_343_000, 16_935_000, 38_297_137.68],
        # Intensity from Trend Analysis sheet
        "Intensity_Revenue":  [82.43, 79.89, 0],
        "Intensity_Employee": [73.95, 76.63, 0],
    })


@st.cache_data(show_spinner=False)
def load_carbon_targets() -> pd.DataFrame:
    """Hardcoded reduction targets from the Carbon Footprint workbook."""
    return pd.DataFrame({
        "Scope":         ["Scope 1+2", "Scope 3"],
        "Baseline_Year": [2019, 2019],
        "Baseline_tCO2e":[11_242_356, 11_399_031],
        "Target_Year":   [2030, 2030],
        "Reduction_Pct": [0.275, 0.275],
        "Target_tCO2e":  [8_150_708, 8_264_297],
        "Annual_Reduction":[281_059, 284_976],
        "Source":        ["Sustainability Report 2023", "Sustainability Report 2023"],
    })


# ─────────────────────────────────────────────
# KPI FORMATTERS
# ─────────────────────────────────────────────
def fmt_number(val: float, decimals: int = 1) -> str:
    if pd.isna(val):
        return "—"
    if abs(val) >= 1_000_000:
        return f"{val/1_000_000:.{decimals}f}M"
    if abs(val) >= 1_000:
        return f"{val/1_000:.{decimals}f}K"
    return f"{val:,.{decimals}f}"


def fmt_pct(val: float, decimals: int = 1) -> str:
    if pd.isna(val):
        return "—"
    return f"{val*100:.{decimals}f}%"


def fmt_score(val: float) -> str:
    if pd.isna(val):
        return "—"
    return f"{val:.2f} / 10"


def quality_badge(score: float) -> str:
    """Return an emoji badge for a 0–100 quality score."""
    if pd.isna(score):
        return "⬜ Not Scored"
    if score >= 80:
        return "✅ High Quality"
    if score >= 60:
        return "🟡 Acceptable"
    return "🔴 Poor Quality"


# ─────────────────────────────────────────────
# REUSABLE UI COMPONENTS
# ─────────────────────────────────────────────
def kpi_card(label: str, value: str, sub: str = "", color: str = "#4caf82") -> str:
    """Return HTML for a styled KPI card."""
    return f"""
    <div style="
        background: linear-gradient(135deg, #1e2a38 0%, #162032 100%);
        border: 1px solid #2e4057;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    ">
        <div style="color:#8da9c4;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:1.4px;margin-bottom:6px;">
            {label}
        </div>
        <div style="color:#e8f4fd;font-size:26px;font-weight:700;line-height:1.1;">
            {value}
        </div>
        <div style="color:{color};font-size:12px;margin-top:5px;font-weight:500;">
            {sub}
        </div>
    </div>"""


def section_header(title: str) -> None:
    st.markdown(
        f"<div style='color:#8da9c4;font-size:10px;font-weight:700;"
        f"letter-spacing:2.5px;text-transform:uppercase;"
        f"border-bottom:1px solid #2e4057;padding-bottom:6px;"
        f"margin-bottom:14px;'>{title}</div>",
        unsafe_allow_html=True,
    )


def peer_rank_color(rank: str) -> str:
    rank = str(rank).strip()
    mapping = {
        "Leading":      "#4caf82",
        "Above Median": "#8bc34a",
        "Median":       "#ffd700",
        "Below Median": "#ff9800",
        "Lagging":      "#e06c75",
    }
    return mapping.get(rank, "#8da9c4")


# ─────────────────────────────────────────────
# STANDARD RADAR METRICS LIST
# ─────────────────────────────────────────────
RADAR_METRICS = [
    "Energy Management",
    "GHG Emissions Mgmt.",
    "Water Management",
    "Waste Management",
    "Air Quality",
    "OH&S Mgmt.",
    "Board Composition",
    "Executive Compensation",
]

# ─────────────────────────────────────────────
# CARBON REDUCTION TRAJECTORY HELPER
# ─────────────────────────────────────────────
def build_trajectory(
    baseline_year: int,
    baseline_val: float,
    target_year: int,
    target_val: float,
) -> pd.DataFrame:
    """Linear trajectory from baseline to target."""
    years = list(range(baseline_year, target_year + 1))
    vals  = np.linspace(baseline_val, target_val, len(years))
    return pd.DataFrame({"Year": years, "Target_tCO2e": vals})
