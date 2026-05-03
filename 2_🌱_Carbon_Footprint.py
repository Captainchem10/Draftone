"""
pages/2_🌱_Carbon_Footprint.py
Full carbon footprint analysis: scope breakdown, trajectory, and intensity.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import (
    load_carbon_trend, load_carbon_targets,
    section_header, kpi_card, dark_layout, fmt_number, build_trajectory,
    DARK_BG, GRID_CLR,
)

st.set_page_config(page_title="Carbon Footprint | SW ESG", page_icon="🌱", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #12192a; border-right: 1px solid #2e4057; }
    #MainMenu, footer { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# ── Load ───────────────────────────────────────────────────────────────────
trend   = load_carbon_trend()
targets = load_carbon_targets()

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌱 Carbon Footprint")
    st.markdown("---")
    show_target = st.checkbox("Show 2030 Target Line", value=True)
    show_intensity = st.checkbox("Show Intensity Metrics", value=True)
    unit_choice = st.radio("Display Unit", ["tCO₂e", "MtCO₂e"], index=1)
    divisor = 1_000_000 if unit_choice == "MtCO₂e" else 1
    unit_label = unit_choice

    st.markdown("---")
    st.markdown("**Reduction Targets**")
    for _, row in targets.iterrows():
        st.markdown(
            f"- **{row['Scope']}**: −{row['Reduction_Pct']*100:.0f}% by {row['Target_Year']}"
        )
    st.caption("Source: SW Sustainability Report 2023")

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("<h2 style='color:#e8f4fd;'>🌱 Carbon Footprint Analysis</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#8da9c4;'>GHG Protocol Framework · Scope 1, 2 & 3 · 2022–2024 · 2030 Targets</p>",
            unsafe_allow_html=True)

# ── KPI Row ────────────────────────────────────────────────────────────────
total_2024 = trend[trend["Year"]==2024]["Total"].values[0] / divisor
total_2023 = trend[trend["Year"]==2023]["Total"].values[0] / divisor
yoy_change = (total_2024 - total_2023) / total_2023 * 100 if total_2023 != 0 else 0

target_s12 = targets[targets["Scope"]=="Scope 1+2"]["Target_tCO2e"].values[0] / divisor
baseline_s12 = targets[targets["Scope"]=="Scope 1+2"]["Baseline_tCO2e"].values[0] / divisor

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("2024 Total Emissions",
                      f"{total_2024:.2f}",
                      f"{unit_label} (Scope 1+2+3)", "#1e90ff"), unsafe_allow_html=True)
c2.markdown(kpi_card("YoY Change 2023→2024",
                      f"{yoy_change:+.1f}%",
                      "vs prior year", "#ff6b35" if yoy_change > 0 else "#4caf82"), unsafe_allow_html=True)
c3.markdown(kpi_card("2030 Scope 1+2 Target",
                      f"{target_s12:.2f}",
                      f"{unit_label} (−27.5% from 2019)", "#4caf82"), unsafe_allow_html=True)
c4.markdown(kpi_card("2019 Scope 1+2 Baseline",
                      f"{baseline_s12:.2f}",
                      f"{unit_label} · Target base year", "#ffd700"), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Main Trend Chart ───────────────────────────────────────────────────────
section_header("ABSOLUTE EMISSIONS TREND")

fig_main = go.Figure()

# Actual total
fig_main.add_trace(go.Scatter(
    x=trend["Year"], y=trend["Total"]/divisor,
    mode="lines+markers", name=f"Actual Total ({unit_label})",
    line=dict(color="#1e90ff", width=3),
    marker=dict(size=9, symbol="circle"),
    fill="tozeroy", fillcolor="rgba(30,144,255,0.08)",
    hovertemplate="<b>%{x}</b><br>%{y:.3f} " + unit_label + "<extra></extra>",
))

# Target trajectory
if show_target:
    for _, trow in targets.iterrows():
        traj = build_trajectory(trow["Baseline_Year"], trow["Baseline_tCO2e"]/divisor,
                                 trow["Target_Year"],   trow["Target_tCO2e"]/divisor)
        # only show from 2022 onward
        traj = traj[traj["Year"] >= 2022]
        fig_main.add_trace(go.Scatter(
            x=traj["Year"], y=traj["Target_tCO2e"],
            mode="lines", name=f"{trow['Scope']} Target 2030",
            line=dict(color="#ff6b35" if "1+2" in trow["Scope"] else "#c678dd",
                      width=2, dash="dash"),
            hovertemplate="<b>%{x}</b><br>Target: %{y:.3f} " + unit_label + "<extra></extra>",
        ))

fig_main.update_layout(**dark_layout(height=380,
    xaxis=dict(dtick=1, title="Year", titlefont=dict(color="#8da9c4")),
    yaxis=dict(title=f"Emissions ({unit_label})", titlefont=dict(color="#8da9c4")),
))
st.plotly_chart(fig_main, use_container_width=True)

# ── Scope Breakdown + Intensity ────────────────────────────────────────────
col_scope, col_int = st.columns([1.2, 1])

with col_scope:
    section_header("SCOPE BREAKDOWN")
    st.markdown("**Scope Contributions (2024)**")
    scope_df = pd.DataFrame({
        "Scope": ["Scope 1 (Direct)", "Scope 2 Market-Based", "Scope 2 Location-Based", "Scope 3"],
        "Value": [
            trend[trend["Year"]==2024]["Scope1"].values[0]/divisor,
            trend[trend["Year"]==2024]["Scope2_MB"].values[0]/divisor,
            trend[trend["Year"]==2024]["Scope2_LB"].values[0]/divisor,
            trend[trend["Year"]==2024]["Scope3"].values[0]/divisor,
        ],
        "Color": ["#1e90ff","#4caf82","#56b6c2","#ffd700"],
    })
    scope_df = scope_df[scope_df["Value"] > 0]

    if scope_df.empty:
        st.info("ℹ️ Scope 2 and 3 data not yet entered in the Carbon Footprint workbook. "
                "Scope 1 shows 2024 calculated value.")
        # Just show Scope 1 bar
        fig_scope = go.Figure(go.Bar(
            x=["Scope 1 (Direct)"],
            y=[trend[trend["Year"]==2024]["Scope1"].values[0]/divisor],
            marker_color="#1e90ff",
            text=[f"{trend[trend['Year']==2024]['Scope1'].values[0]/divisor:.2f}"],
            textposition="outside", textfont=dict(color="#e8f4fd"),
        ))
    else:
        fig_scope = go.Figure(go.Bar(
            x=scope_df["Scope"], y=scope_df["Value"],
            marker_color=scope_df["Color"].tolist(),
            text=scope_df["Value"].apply(lambda v: f"{v:.3f}"),
            textposition="outside", textfont=dict(color="#e8f4fd"),
        ))

    fig_scope.update_layout(**dark_layout(height=300,
        yaxis=dict(title=f"Emissions ({unit_label})", titlefont=dict(color="#8da9c4")),
        showlegend=False,
    ))
    st.plotly_chart(fig_scope, use_container_width=True)

with col_int:
    section_header("CARBON INTENSITY")
    if show_intensity:
        st.markdown("**Carbon Intensity Trends**")
        int_df = trend[trend["Intensity_Revenue"] > 0][["Year","Intensity_Revenue","Intensity_Employee"]]

        fig_int = go.Figure()
        fig_int.add_trace(go.Scatter(
            x=int_df["Year"], y=int_df["Intensity_Revenue"],
            mode="lines+markers", name="tCO₂e / $M Revenue",
            line=dict(color="#4caf82", width=2.5),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>%{y:.2f} tCO₂e/$M<extra></extra>",
        ))
        fig_int.add_trace(go.Scatter(
            x=int_df["Year"], y=int_df["Intensity_Employee"],
            mode="lines+markers", name="tCO₂e / FTE",
            line=dict(color="#ffd700", width=2.5),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>%{y:.2f} tCO₂e/FTE<extra></extra>",
        ))
        fig_int.update_layout(**dark_layout(height=300,
            yaxis=dict(title="Intensity", titlefont=dict(color="#8da9c4")),
            xaxis=dict(dtick=1, title="Year", titlefont=dict(color="#8da9c4")),
        ))
        st.plotly_chart(fig_int, use_container_width=True)
    else:
        st.info("Enable 'Show Intensity Metrics' in the sidebar.")

# ── Targets Table ──────────────────────────────────────────────────────────
section_header("REDUCTION TARGETS DETAIL")
tgt_display = targets.copy()
tgt_display["Baseline_tCO2e"] = tgt_display["Baseline_tCO2e"].apply(lambda x: f"{x:,.0f} tCO₂e")
tgt_display["Target_tCO2e"]   = tgt_display["Target_tCO2e"].apply(lambda x: f"{x:,.0f} tCO₂e")
tgt_display["Reduction_Pct"]  = tgt_display["Reduction_Pct"].apply(lambda x: f"{x*100:.1f}%")
tgt_display["Annual_Reduction"]= tgt_display["Annual_Reduction"].apply(lambda x: f"{x:,.0f} tCO₂e/yr")
tgt_display.columns = ["Scope","Baseline Year","Baseline Emissions",
                         "Target Year","Reduction %","Target Emissions",
                         "Required Annual Cut","Source"]
st.dataframe(tgt_display, use_container_width=True, hide_index=True)

st.caption("GHG Protocol Framework · EY Limited Assurance (legacy WestRock) · SW Sustainability Report 2024")
