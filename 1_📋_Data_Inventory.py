"""
pages/1_📋_Data_Inventory.py
Deep-dive view of the ESG Data Inventory with quality scoring.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import (
    load_esg, load_inventory_scored,
    section_header, kpi_card, dark_layout, quality_badge,
    PILLAR_COLORS, PILLAR_LABELS, BIZ_COLORS, BIZ_LABELS,
    QUALITY_COLORS, fmt_number,
)

st.set_page_config(page_title="Data Inventory | SW ESG", page_icon="📋", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #12192a; border-right: 1px solid #2e4057; }
    #MainMenu, footer { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# ── Load ───────────────────────────────────────────────────────────────────
esg = load_esg()

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 Data Inventory")
    st.markdown("---")
    pillars = sorted(esg["Pillar"].dropna().unique())
    sel_pillars = st.multiselect("Pillar", pillars, default=pillars)
    cats = sorted(esg["KPI_Category"].dropna().unique())
    sel_cats = st.multiselect("KPI Category", cats, default=cats)
    bizs = sorted(esg["Business"].dropna().unique())
    sel_biz = st.multiselect("Business Unit", bizs, default=bizs,
                              help="S=Smurfit Kappa · W=WestRock · SW=Combined")
    yr_min, yr_max = int(esg["Reporting_Year"].min()), int(esg["Reporting_Year"].max())
    year_range = st.slider("Year Range", yr_min, yr_max, (yr_min, yr_max))
    metric_search = st.text_input("🔍 Search KPI Name", "")

# ── Filter ─────────────────────────────────────────────────────────────────
df = esg[
    esg["Pillar"].isin(sel_pillars) &
    esg["KPI_Category"].isin(sel_cats) &
    esg["Business"].isin(sel_biz) &
    esg["Reporting_Year"].between(year_range[0], year_range[1])
].copy()

if metric_search:
    df = df[df["KPI_Name"].str.contains(metric_search, case=False, na=False)]

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("<h2 style='color:#e8f4fd;'>📋 ESG Data Inventory</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#8da9c4;'>30+ KPIs · Multi-year · Quality Scored</p>", unsafe_allow_html=True)

# ── KPI Row ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Total Records", f"{len(df):,}", "in filtered view"), unsafe_allow_html=True)
c2.markdown(kpi_card("Unique KPIs", f"{df['KPI_Name'].nunique():,}", "distinct metrics"), unsafe_allow_html=True)
c3.markdown(kpi_card("Years Covered", f"{df['Reporting_Year'].nunique()}", f"{yr_min}–{yr_max}"), unsafe_allow_html=True)
c4.markdown(kpi_card("Business Units", f"{df['Business'].nunique()}", ", ".join(sorted(df['Business'].unique()))), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row 1 ───────────────────────────────────────────────────────────
section_header("KPI DISTRIBUTION")
col_pie, col_cat = st.columns([1, 1.5])

with col_pie:
    st.markdown("**KPI Count by Pillar**")
    pillar_counts = df.groupby("Pillar").size().reset_index(name="Count")
    pillar_counts["Label"] = pillar_counts["Pillar"].map(PILLAR_LABELS).fillna(pillar_counts["Pillar"])
    pillar_counts["Color"] = pillar_counts["Pillar"].map(PILLAR_COLORS)
    fig_pie = go.Figure(go.Pie(
        labels=pillar_counts["Label"],
        values=pillar_counts["Count"],
        hole=0.55,
        marker=dict(colors=pillar_counts["Color"].tolist(), line=dict(color="#0e1117", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#e8f4fd", size=11),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    fig_pie.update_layout(**dark_layout(height=300, margin=dict(l=10,r=10,t=20,b=10),
                                        showlegend=False))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_cat:
    st.markdown("**KPI Records by Category & Year**")
    cat_yr = df.groupby(["KPI_Category", "Reporting_Year"]).size().reset_index(name="Count")
    fig_cat = px.bar(cat_yr, x="Reporting_Year", y="Count", color="KPI_Category",
                     barmode="stack", labels={"Count":"Records","Reporting_Year":"Year","KPI_Category":"Category"})
    fig_cat.update_layout(**dark_layout(height=300, legend=dict(font=dict(color="#c0d8f0",size=10),
                                                                  bgcolor="#162032")))
    st.plotly_chart(fig_cat, use_container_width=True)

# ── Charts Row 2 ───────────────────────────────────────────────────────────
section_header("VALUE TRENDS")
col_trend, col_biz = st.columns([1.5, 1])

with col_trend:
    st.markdown("**KPI Total Value Over Time by Category**")
    trend = df.groupby(["KPI_Category", "Reporting_Year"])["Total_Value"].sum().reset_index()
    fig_trend = px.line(trend, x="Reporting_Year", y="Total_Value", color="KPI_Category",
                        markers=True, labels={"Total_Value":"Value","Reporting_Year":"Year","KPI_Category":"Category"})
    fig_trend.update_layout(**dark_layout(height=340))
    fig_trend.update_traces(line=dict(width=2), marker=dict(size=6))
    st.plotly_chart(fig_trend, use_container_width=True)

with col_biz:
    st.markdown("**2024 Value by Business & Pillar**")
    d24 = df[df["Reporting_Year"] == df["Reporting_Year"].max()]
    biz_pil = d24.groupby(["Business","Pillar"])["Total_Value"].sum().reset_index()
    biz_pil["Pillar_Label"] = biz_pil["Pillar"].map(PILLAR_LABELS).fillna(biz_pil["Pillar"])
    fig_biz = px.bar(biz_pil, x="Business", y="Total_Value", color="Pillar_Label",
                     barmode="group", color_discrete_map={v:PILLAR_COLORS.get(k,"#aaa") for k,v in PILLAR_LABELS.items()},
                     labels={"Total_Value":"Value","Business":"Business Unit"})
    fig_biz.update_layout(**dark_layout(height=340, legend=dict(font=dict(color="#c0d8f0",size=10))))
    st.plotly_chart(fig_biz, use_container_width=True)

# ── Data Table ─────────────────────────────────────────────────────────────
section_header("RAW DATA TABLE")
display = df[["Pillar","KPI_Category","KPI_Name","Total_Value","Business","Unit","Reporting_Year"]].copy()
display["Pillar"]   = display["Pillar"].map(PILLAR_LABELS).fillna(display["Pillar"])
display["Business"] = display["Business"].map(BIZ_LABELS).fillna(display["Business"])
display["Total_Value"] = display["Total_Value"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "—")
display = display.rename(columns={
    "KPI_Category":"Category","KPI_Name":"KPI",
    "Total_Value":"Value","Reporting_Year":"Year",
})
st.dataframe(display.reset_index(drop=True), use_container_width=True, height=380)

st.caption(f"Showing {len(df):,} of {len(esg):,} total records · "
           f"Smurfit Westrock ESG Data Inventory · May 2026")
