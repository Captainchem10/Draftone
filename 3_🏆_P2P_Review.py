"""
pages/3_🏆_P2P_Review.py
Full peer-to-peer ESG score review with radar, heatmap, ranking, and drilldown.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import (
    load_p2p, section_header, kpi_card, dark_layout, fmt_score, peer_rank_color,
    COMPANY_MAP, COMPANY_COLORS, RADAR_METRICS, DARK_BG, GRID_CLR,
)

st.set_page_config(page_title="P2P Review | SW ESG", page_icon="🏆", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #12192a; border-right: 1px solid #2e4057; }
    #MainMenu, footer { visibility: hidden; }
    .rank-badge {
        display:inline-block; padding:2px 10px; border-radius:20px;
        font-size:11px; font-weight:700; letter-spacing:.5px;
    }
</style>""", unsafe_allow_html=True)

# ── Load ───────────────────────────────────────────────────────────────────
p2p_df, mktcap_df = load_p2p()

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏆 P2P Review")
    st.markdown("---")
    all_companies = sorted(p2p_df["Company"].unique())
    sel_companies = st.multiselect("Companies", all_companies, default=all_companies,
                                   format_func=lambda x: COMPANY_MAP.get(x, x))
    all_pilars = sorted(p2p_df["Pilar"].dropna().unique())
    sel_pilar = st.selectbox("Pillar Focus", ["All"] + list(all_pilars))
    highlight = st.selectbox("Highlight Company",
                              ["None"] + all_companies,
                              format_func=lambda x: COMPANY_MAP.get(x, x) if x != "None" else "None")
    chart_type = st.radio("Radar Display", ["ESG Sub-Metrics", "ESG Pillars"], index=0)
    st.markdown("---")
    st.markdown("**Score Scale:** 0–10 per metric")
    st.caption("Source: MSCI · Sustainalytics · S&P Global ESG · Rep Risk")

# ── Filter ─────────────────────────────────────────────────────────────────
df = p2p_df[p2p_df["Company"].isin(sel_companies)].copy()
if sel_pilar != "All":
    df_view = df[df["Pilar"] == sel_pilar]
else:
    df_view = df.copy()

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("<h2 style='color:#e8f4fd;'>🏆 Peer-to-Peer ESG Review</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#8da9c4;'>MSCI · Sustainalytics · S&P Global · 6 Peers · Paper & Packaging Sector</p>",
            unsafe_allow_html=True)

# ── KPI Row (SW position vs peers) ─────────────────────────────────────────
esg_scores = p2p_df[(p2p_df["Pilar"]=="ESG") & p2p_df["Company"].isin(sel_companies)]
totals = esg_scores.groupby("Company")["Score"].sum().sort_values(ascending=False)
sw_score = totals.get("SW", 0)
sw_rank  = (list(totals.index).index("SW") + 1) if "SW" in totals.index else "N/A"
peer_avg = totals.mean()
best_co  = COMPANY_MAP.get(totals.idxmax(), totals.idxmax())

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("SW Total ESG Score", f"{sw_score:.2f}",
                      f"Sum across {len(esg_scores[esg_scores['Company']=='SW'])} pillars", "#1e90ff"), unsafe_allow_html=True)
c2.markdown(kpi_card("SW Peer Rank", f"#{sw_rank} of {len(sel_companies)}",
                      "by total ESG score", "#ffd700"), unsafe_allow_html=True)
c3.markdown(kpi_card("Peer Average Score", f"{peer_avg:.2f}",
                      "across selected companies", "#8da9c4"), unsafe_allow_html=True)
c4.markdown(kpi_card("Sector Leader", best_co,
                      f"Score: {totals.max():.2f}", "#4caf82"), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Radar + Ranking ────────────────────────────────────────────────────────
section_header("COMPETITIVE POSITIONING")
col_radar, col_rank = st.columns([1.2, 0.8])

with col_radar:
    if chart_type == "ESG Sub-Metrics":
        st.markdown("**Radar — 8 Key Sub-Metrics**")
        radar_data  = df[df["Metric"].isin(RADAR_METRICS)]
        radar_pivot = radar_data.pivot_table(
            index="Metric", columns="Company", values="Score", aggfunc="mean"
        ).reindex(RADAR_METRICS).fillna(0)
        cats = RADAR_METRICS + [RADAR_METRICS[0]]

        fig_radar = go.Figure()
        for company in radar_pivot.columns:
            vals = radar_pivot[company].tolist()
            opacity = 1.0 if (highlight == "None" or company == highlight) else 0.35
            fig_radar.add_trace(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats, fill="toself",
                fillcolor=COMPANY_COLORS.get(company,"#aaa")+"33",
                line=dict(color=COMPANY_COLORS.get(company,"#aaa"), width=2 if opacity==1 else 1),
                name=COMPANY_MAP.get(company,company),
                opacity=opacity,
                hovertemplate="<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>",
            ))
    else:
        st.markdown("**Radar — ESG Pillar Scores**")
        pillar_data = df[df["Pilar"]=="ESG"].copy()
        piv = pillar_data.pivot_table(
            index="Metric", columns="Company", values="Score", aggfunc="mean"
        ).fillna(0)
        metrics = piv.index.tolist()
        cats = metrics + [metrics[0]]
        fig_radar = go.Figure()
        for company in piv.columns:
            vals = piv[company].tolist()
            opacity = 1.0 if (highlight == "None" or company == highlight) else 0.35
            fig_radar.add_trace(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats, fill="toself",
                fillcolor=COMPANY_COLORS.get(company,"#aaa")+"33",
                line=dict(color=COMPANY_COLORS.get(company,"#aaa"), width=2 if opacity==1 else 1),
                name=COMPANY_MAP.get(company,company),
                opacity=opacity,
            ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0,10],
                            tickfont=dict(color="#8da9c4",size=9),
                            gridcolor=GRID_CLR, linecolor=GRID_CLR),
            angularaxis=dict(tickfont=dict(color="#c0d8f0",size=10),
                             gridcolor=GRID_CLR, linecolor=GRID_CLR),
            bgcolor=DARK_BG,
        ),
        paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
        legend=dict(font=dict(color="#c0d8f0"), bgcolor=DARK_BG),
        margin=dict(l=40,r=40,t=30,b=30), height=440,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with col_rank:
    st.markdown("**Company ESG Rankings**")
    rank_df = totals.reset_index()
    rank_df.columns = ["Company", "Total_Score"]
    rank_df["Rank"] = range(1, len(rank_df)+1)
    rank_df["Name"] = rank_df["Company"].map(COMPANY_MAP)
    rank_df["Color"] = rank_df["Company"].map(COMPANY_COLORS)

    fig_rank = go.Figure()
    for _, row in rank_df.iterrows():
        opacity = 1.0 if (highlight == "None" or row["Company"] == highlight) else 0.4
        fig_rank.add_trace(go.Bar(
            x=[row["Total_Score"]], y=[f"#{row['Rank']} {row['Name']}"],
            orientation="h", name=row["Name"],
            marker_color=row["Color"],
            opacity=opacity,
            text=f"{row['Total_Score']:.2f}",
            textposition="outside",
            textfont=dict(color="#e8f4fd", size=11),
            hovertemplate=f"<b>{row['Name']}</b><br>Score: {row['Total_Score']:.2f}<extra></extra>",
        ))

    fig_rank.update_layout(**dark_layout(height=440, showlegend=False,
        xaxis=dict(title="Total ESG Score", range=[0, rank_df["Total_Score"].max()*1.3],
                   titlefont=dict(color="#8da9c4")),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20,r=60,t=20,b=40),
        bargap=0.35,
    ))
    st.plotly_chart(fig_rank, use_container_width=True)

# ── Heatmap ────────────────────────────────────────────────────────────────
section_header("SCORE HEATMAP")
heat_data  = p2p_df[p2p_df["Company"].isin(sel_companies)]
if sel_pilar != "All":
    heat_data = heat_data[heat_data["Pilar"] == sel_pilar]
heat_pivot = heat_data.pivot_table(
    index="Metric", columns="Company", values="Score", aggfunc="mean"
).fillna(0)
heat_pivot.columns = [COMPANY_MAP.get(c,c) for c in heat_pivot.columns]

fig_heat = go.Figure(data=go.Heatmap(
    z=heat_pivot.values,
    x=heat_pivot.columns.tolist(),
    y=heat_pivot.index.tolist(),
    colorscale=[[0,"#1a1a2e"],[0.25,"#16213e"],[0.5,"#0f3460"],[0.75,"#1a6498"],[1,"#1e90ff"]],
    text=np.round(heat_pivot.values, 2),
    texttemplate="%{text}",
    textfont=dict(size=10, color="white"),
    hovertemplate="<b>%{x}</b><br>%{y}<br>Score: %{z:.2f}<extra></extra>",
    showscale=True,
    colorbar=dict(
        title=dict(text="Score", font=dict(color="#8da9c4")),
        tickfont=dict(color="#8da9c4"),
    ),
))
fig_heat.update_layout(**dark_layout(
    height=max(350, len(heat_pivot)*28),
    margin=dict(l=20,r=80,t=20,b=20),
    xaxis=dict(tickfont=dict(color="#c0d8f0")),
    yaxis=dict(tickfont=dict(color="#c0d8f0")),
))
st.plotly_chart(fig_heat, use_container_width=True)

# ── Detail Table ───────────────────────────────────────────────────────────
section_header("DETAILED SCORE TABLE")
col_filter, _ = st.columns([2,3])
with col_filter:
    metric_search = st.text_input("🔍 Search metric", "")

detail = df_view[["Company","Pilar","Metric","Weight","Score","Disclosure","Peer Rank"]].copy()
detail["Company"] = detail["Company"].map(lambda x: COMPANY_MAP.get(x,x))
detail["Score"]   = detail["Score"].round(2)
detail["Weight"]  = detail["Weight"].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "—")

if metric_search:
    detail = detail[detail["Metric"].str.contains(metric_search, case=False, na=False)]

# Colour the Peer Rank column
def color_rank(val):
    c = peer_rank_color(str(val))
    return f"color: {c}; font-weight: 600;"

styled = detail.reset_index(drop=True).style.applymap(
    color_rank, subset=["Peer Rank"]
)
st.dataframe(styled, use_container_width=True, height=360)

# ── Market Cap Reference ────────────────────────────────────────────────────
section_header("MARKET CONTEXT")
mc = mktcap_df[["Tick","Name","Market Capital","Revenue (B)"]].copy()
mc["Market Capital"] = mc["Market Capital"].apply(lambda x: f"${x/1e9:.2f}B" if pd.notna(x) else "—")
mc["Revenue (B)"]    = mc["Revenue (B)"].apply(lambda x: f"${x:.2f}B" if pd.notna(x) else "—")
st.dataframe(mc, use_container_width=True, hide_index=True)

st.caption("Ratings: MSCI ESG · Sustainalytics Risk Score · S&P Global ESG Rank · Rep Risk · May 2026")
