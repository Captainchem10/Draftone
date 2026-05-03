"""
Smurfit Westrock ESG Dashboard
Streamlit app combining Data Inventory, Carbon Footprint, and P2P Review data.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Smurfit Westrock ESG Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0e1117; }

    /* KPI card */
    .kpi-card {
        background: linear-gradient(135deg, #1e2a38 0%, #162032 100%);
        border: 1px solid #2e4057;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .kpi-label {
        color: #8da9c4;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 6px;
    }
    .kpi-value {
        color: #e8f4fd;
        font-size: 28px;
        font-weight: 700;
        line-height: 1.1;
    }
    .kpi-sub {
        color: #4caf82;
        font-size: 12px;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Section headers */
    .section-header {
        color: #8da9c4;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        border-bottom: 1px solid #2e4057;
        padding-bottom: 6px;
        margin-bottom: 16px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #12192a;
        border-right: 1px solid #2e4057;
    }

    /* Remove Streamlit branding */
    #MainMenu, footer { visibility: hidden; }

    /* Chart containers */
    .chart-container {
        background: #162032;
        border-radius: 12px;
        border: 1px solid #2e4057;
        padding: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    # ── Data Inventory (ESG sheet) ──────────────────────────────────────────
    esg = pd.read_excel(
        "05022026_SW_Data_Inventory.xlsx",
        sheet_name="ESG",
        engine="openpyxl",
    )
    esg.columns = [
        "Pillar", "KPI_Category", "KPI_Name",
        "Total_Value", "Business", "Unit",
        "Reporting_Year", "Unit_per_Revenue", "Unit_per_MarketCap",
    ]
    esg["Total_Value"] = pd.to_numeric(esg["Total_Value"], errors="coerce")
    esg["Reporting_Year"] = pd.to_numeric(esg["Reporting_Year"], errors="coerce")

    # ── P2P Review Dashboard sheet ─────────────────────────────────────────
    p2p_raw = pd.read_excel(
        "SW_P2P_Review.xlsx",
        sheet_name="Dashboard",
        engine="openpyxl",
    )
    p2p = p2p_raw[
        ["Company", "Pilar", "Metric", "Weight", "Score", "Disclosure", "Peer Rank"]
    ].dropna(subset=["Company"])
    p2p["Score"] = pd.to_numeric(p2p["Score"], errors="coerce")
    p2p["Weight"] = pd.to_numeric(p2p["Weight"], errors="coerce")

    # Market cap
    mktcap = pd.read_excel(
        "SW_P2P_Review.xlsx",
        sheet_name="Market Cap",
        engine="openpyxl",
    )

    # ── Carbon Footprint Trend Analysis ────────────────────────────────────
    trend_raw = pd.read_excel(
        "SW_Carbon_Footprint.xlsx",
        sheet_name="Trend Analysis",
        engine="openpyxl",
    )
    # Row 9 contains the TOTAL row: Unnamed:0 = metric, cols 1/2/3 = years
    # The year header row is row 4 (index), data starts row 5
    # Let's manually extract what we can confirm from the sheet
    carbon_trend = pd.DataFrame({
        "Year":   [2022, 2023, 2024],
        "S1_S2_S3": [16_343_000, 16_935_000, 38_297_137.68],
    })

    return esg, p2p, mktcap, carbon_trend


esg_df, p2p_df, mktcap_df, carbon_trend = load_data()


# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Smurfit_Westrock_logo.svg/320px-Smurfit_Westrock_logo.svg.png",
        use_container_width=True,
    )
    st.markdown("---")
    st.markdown("### 🔍 Filters")

    # Pillar filter
    all_pillars = sorted(esg_df["Pillar"].dropna().unique().tolist())
    selected_pillars = st.multiselect(
        "ESG Pillar",
        options=all_pillars,
        default=all_pillars,
    )

    # KPI Category filter
    all_cats = sorted(esg_df["KPI_Category"].dropna().unique().tolist())
    selected_cats = st.multiselect(
        "KPI Category",
        options=all_cats,
        default=all_cats,
    )

    # Business filter
    all_biz = sorted(esg_df["Business"].dropna().unique().tolist())
    selected_biz = st.multiselect(
        "Business Unit",
        options=all_biz,
        default=all_biz,
        help="S = Smurfit Kappa, W = WestRock, SW = Combined",
    )

    # Year range
    min_yr = int(esg_df["Reporting_Year"].min())
    max_yr = int(esg_df["Reporting_Year"].max())
    year_range = st.slider(
        "Reporting Year Range",
        min_value=min_yr,
        max_value=max_yr,
        value=(min_yr, max_yr),
    )

    # P2P filter
    st.markdown("---")
    st.markdown("### 🏭 Peer Review Filters")
    all_companies = sorted(p2p_df["Company"].unique().tolist())
    company_map = {
        "SW": "Smurfit Westrock",
        "PKG": "Packaging Corp",
        "IP": "Intl Paper",
        "GPI": "Graphic Packaging",
        "SK": "Smurfit Kappa",
        "WK": "WestRock",
    }
    selected_companies = st.multiselect(
        "Companies",
        options=all_companies,
        default=all_companies,
        format_func=lambda x: company_map.get(x, x),
    )

    all_pilars = sorted(p2p_df["Pilar"].dropna().unique().tolist())
    selected_pilar = st.selectbox(
        "P2P Focus Pillar",
        options=["All"] + all_pilars,
    )

    st.markdown("---")
    st.caption("📊 Smurfit Westrock ESG Dashboard · May 2026")


# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
filtered_esg = esg_df[
    esg_df["Pillar"].isin(selected_pillars)
    & esg_df["KPI_Category"].isin(selected_cats)
    & esg_df["Business"].isin(selected_biz)
    & esg_df["Reporting_Year"].between(year_range[0], year_range[1])
].copy()

filtered_p2p = p2p_df[p2p_df["Company"].isin(selected_companies)].copy()
if selected_pilar != "All":
    filtered_p2p = filtered_p2p[filtered_p2p["Pilar"] == selected_pilar]


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#e8f4fd;font-size:2rem;margin-bottom:4px;'>🌍 Smurfit Westrock ESG Dashboard</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#8da9c4;font-size:14px;margin-bottom:24px;'>"
    "GHG Protocol Framework · ESG Data Inventory · Peer-to-Peer Review · May 2026</p>",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# KPI BOXES (TOP ROW)
# ─────────────────────────────────────────────
total_val = filtered_esg["Total_Value"].sum()
avg_val = filtered_esg["Total_Value"].mean()
kpi_count = len(filtered_esg)
quality_score_2024 = 75  # representative overall quality score

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total KPI Value (Sum)</div>
        <div class="kpi-value">{total_val:,.0f}</div>
        <div class="kpi-sub">Across {kpi_count} data points</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Average KPI Value</div>
        <div class="kpi-value">{avg_val:,.1f}</div>
        <div class="kpi-sub">Per metric · filtered view</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">KPI Record Count</div>
        <div class="kpi-value">{kpi_count:,}</div>
        <div class="kpi-sub">ESG metrics tracked</div>
    </div>""", unsafe_allow_html=True)

with col4:
    esg_score_sw = p2p_df[p2p_df["Company"] == "SW"][p2p_df["Pilar"] == "ESG"]["Score"].sum()
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">SW ESG Composite Score</div>
        <div class="kpi-value">{esg_score_sw:.2f}</div>
        <div class="kpi-sub">vs Peer Avg: 16.9 pts</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ROW 1: WEB / RADAR CHART (P2P)  +  PEER TOTAL SCORES BAR
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">PEER-TO-PEER REVIEW</div>', unsafe_allow_html=True)
col_radar, col_bar = st.columns([1.1, 0.9])

# ── Radar Chart ──────────────────────────────────────────────────────────────
with col_radar:
    st.markdown("**Scores by Company – ESG Sub-Metrics (Radar)**")

    # Use ESG pillar sub-metrics that all companies share
    radar_metrics = [
        "Energy Management", "GHG Emissions Mgmt.", "Water Management",
        "Waste Management", "Air Quality", "OH&S Mgmt.",
        "Board Composition", "Executive Compensation",
    ]

    radar_data = filtered_p2p[filtered_p2p["Metric"].isin(radar_metrics)].copy()
    radar_pivot = radar_data.pivot_table(
        index="Metric", columns="Company", values="Score", aggfunc="mean"
    ).reindex(radar_metrics)

    color_map = {
        "SW": "#1e90ff", "PKG": "#ff6b35", "IP": "#4caf82",
        "GPI": "#ffd700", "SK": "#c678dd", "WK": "#56b6c2",
    }

    fig_radar = go.Figure()
    categories = radar_metrics + [radar_metrics[0]]  # close the polygon

    for company in radar_pivot.columns:
        if company not in selected_companies:
            continue
        values = radar_pivot[company].tolist()
        values_closed = values + [values[0]]
        fig_radar.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories,
            fill="toself",
            fillcolor=color_map.get(company, "#ffffff") + "33",
            line=dict(color=color_map.get(company, "#ffffff"), width=2),
            name=company_map.get(company, company),
            hovertemplate="<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>",
        ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 10],
                tickfont=dict(color="#8da9c4", size=9),
                gridcolor="#2e4057",
                linecolor="#2e4057",
            ),
            angularaxis=dict(
                tickfont=dict(color="#c0d8f0", size=10),
                gridcolor="#2e4057",
                linecolor="#2e4057",
            ),
            bgcolor="#162032",
        ),
        paper_bgcolor="#162032",
        plot_bgcolor="#162032",
        legend=dict(font=dict(color="#c0d8f0"), bgcolor="#162032"),
        margin=dict(l=40, r=40, t=30, b=30),
        height=440,
    )
    st.plotly_chart(fig_radar, use_container_width=True)


# ── Peer Total Scores Grouped Bar ────────────────────────────────────────────
with col_bar:
    st.markdown("**Total ESG Score by Company & Pillar**")

    esg_level = p2p_df[
        (p2p_df["Pilar"] == "ESG") & (p2p_df["Company"].isin(selected_companies))
    ].copy()

    esg_level["Weighted"] = esg_level["Score"] * esg_level["Weight"]
    bar_data = esg_level.groupby("Company")["Score"].sum().reset_index()
    bar_data["Company_Label"] = bar_data["Company"].map(company_map)
    bar_data = bar_data.sort_values("Score", ascending=False)

    fig_bar = go.Figure()
    for _, row in bar_data.iterrows():
        c = row["Company"]
        fig_bar.add_trace(go.Bar(
            x=[row["Company_Label"]],
            y=[row["Score"]],
            name=row["Company_Label"],
            marker_color=color_map.get(c, "#aaaaaa"),
            text=f"{row['Score']:.2f}",
            textposition="outside",
            textfont=dict(color="#e8f4fd", size=11),
        ))

    fig_bar.update_layout(
        showlegend=False,
        paper_bgcolor="#162032",
        plot_bgcolor="#162032",
        xaxis=dict(tickfont=dict(color="#c0d8f0"), gridcolor="#2e4057"),
        yaxis=dict(
            title="Sum of ESG Scores",
            titlefont=dict(color="#8da9c4"),
            tickfont=dict(color="#8da9c4"),
            gridcolor="#2e4057",
            range=[0, max(bar_data["Score"]) * 1.25],
        ),
        margin=dict(l=40, r=20, t=30, b=30),
        height=440,
        bargap=0.3,
    )
    st.plotly_chart(fig_bar, use_container_width=True)


# ─────────────────────────────────────────────
# ROW 2: LINE CHART – KPI by Business, Year, Sum 2024
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">DATA INVENTORY — TREND BY BUSINESS & YEAR</div>', unsafe_allow_html=True)

col_line, col_sum24 = st.columns([2, 1])

with col_line:
    st.markdown("**KPI Total Value by Business Unit & Reporting Year**")

    line_data = (
        esg_df.groupby(["Business", "Reporting_Year"])["Total_Value"]
        .sum()
        .reset_index()
        .dropna()
    )

    biz_labels = {"S": "Smurfit Kappa (S)", "W": "WestRock (W)", "SW": "Combined (SW)"}
    biz_colors = {"S": "#1e90ff", "W": "#ff6b35", "SW": "#4caf82"}

    fig_line = go.Figure()
    for biz in sorted(line_data["Business"].unique()):
        if biz not in selected_biz:
            continue
        biz_df = line_data[line_data["Business"] == biz].sort_values("Reporting_Year")
        fig_line.add_trace(go.Scatter(
            x=biz_df["Reporting_Year"],
            y=biz_df["Total_Value"],
            mode="lines+markers",
            name=biz_labels.get(biz, biz),
            line=dict(color=biz_colors.get(biz, "#aaa"), width=2.5),
            marker=dict(size=7, color=biz_colors.get(biz, "#aaa")),
            hovertemplate="<b>%{x}</b><br>Value: %{y:,.1f}<extra></extra>",
        ))

    fig_line.update_layout(
        paper_bgcolor="#162032",
        plot_bgcolor="#162032",
        xaxis=dict(
            title="Reporting Year",
            titlefont=dict(color="#8da9c4"),
            tickfont=dict(color="#8da9c4"),
            gridcolor="#2e4057",
            dtick=1,
        ),
        yaxis=dict(
            title="Sum of KPI Values",
            titlefont=dict(color="#8da9c4"),
            tickfont=dict(color="#8da9c4"),
            gridcolor="#2e4057",
        ),
        legend=dict(font=dict(color="#c0d8f0"), bgcolor="#162032"),
        margin=dict(l=40, r=20, t=20, b=40),
        height=360,
    )
    st.plotly_chart(fig_line, use_container_width=True)


with col_sum24:
    st.markdown("**2024 KPI Sum by Business & Category**")

    data_2024 = esg_df[esg_df["Reporting_Year"] == 2024].copy()
    sum_2024 = (
        data_2024.groupby(["Business", "KPI_Category"])["Total_Value"]
        .sum()
        .reset_index()
        .dropna()
    )

    if sum_2024.empty:
        # Fallback: use latest available year
        latest_yr = esg_df["Reporting_Year"].max()
        data_latest = esg_df[esg_df["Reporting_Year"] == latest_yr]
        sum_2024 = (
            data_latest.groupby(["Business", "KPI_Category"])["Total_Value"]
            .sum()
            .reset_index()
            .dropna()
        )

    sum_2024 = sum_2024[sum_2024["Business"].isin(selected_biz)]

    fig_sum = px.bar(
        sum_2024,
        x="KPI_Category",
        y="Total_Value",
        color="Business",
        barmode="group",
        color_discrete_map=biz_colors,
        labels={"Total_Value": "Sum of Values", "KPI_Category": "Category"},
    )
    fig_sum.update_layout(
        paper_bgcolor="#162032",
        plot_bgcolor="#162032",
        xaxis=dict(tickfont=dict(color="#8da9c4"), gridcolor="#2e4057", tickangle=-30),
        yaxis=dict(tickfont=dict(color="#8da9c4"), gridcolor="#2e4057"),
        legend=dict(font=dict(color="#c0d8f0"), bgcolor="#162032", title="Business"),
        margin=dict(l=20, r=20, t=20, b=60),
        height=360,
    )
    st.plotly_chart(fig_sum, use_container_width=True)


# ─────────────────────────────────────────────
# ROW 3: CARBON FOOTPRINT TREND
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">CARBON FOOTPRINT — EMISSIONS TREND (tCO₂e)</div>', unsafe_allow_html=True)

col_carbon, col_targets = st.columns([2, 1])

with col_carbon:
    st.markdown("**Total Emissions Trend (Scope 1 + 2 + 3) — tCO₂e**")

    targets = pd.DataFrame({
        "Year": [2019, 2030],
        "Scope_1_2_Target": [11_242_356, 8_150_708],
    })

    fig_carbon = go.Figure()

    # Actual trend
    fig_carbon.add_trace(go.Scatter(
        x=carbon_trend["Year"],
        y=carbon_trend["S1_S2_S3"],
        mode="lines+markers",
        name="Actual Emissions",
        line=dict(color="#1e90ff", width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} tCO₂e<extra></extra>",
    ))

    # Target line
    fig_carbon.add_trace(go.Scatter(
        x=targets["Year"],
        y=targets["Scope_1_2_Target"],
        mode="lines+markers",
        name="2030 Reduction Target (−27.5%)",
        line=dict(color="#ff6b35", width=2, dash="dash"),
        marker=dict(size=8, symbol="diamond"),
        hovertemplate="<b>%{x}</b><br>Target: %{y:,.0f} tCO₂e<extra></extra>",
    ))

    fig_carbon.add_annotation(
        x=2024, y=carbon_trend["S1_S2_S3"].iloc[-1],
        text=f"2024: {carbon_trend['S1_S2_S3'].iloc[-1]/1e6:.1f}M tCO₂e",
        showarrow=True, arrowhead=2,
        font=dict(color="#4caf82", size=11),
        arrowcolor="#4caf82",
        bgcolor="#162032",
    )

    fig_carbon.update_layout(
        paper_bgcolor="#162032",
        plot_bgcolor="#162032",
        xaxis=dict(
            title="Year", titlefont=dict(color="#8da9c4"),
            tickfont=dict(color="#8da9c4"), gridcolor="#2e4057", dtick=1,
        ),
        yaxis=dict(
            title="Emissions (tCO₂e)",
            titlefont=dict(color="#8da9c4"),
            tickfont=dict(color="#8da9c4"),
            gridcolor="#2e4057",
        ),
        legend=dict(font=dict(color="#c0d8f0"), bgcolor="#162032"),
        margin=dict(l=40, r=20, t=20, b=40),
        height=320,
    )
    st.plotly_chart(fig_carbon, use_container_width=True)


with col_targets:
    st.markdown("**Reduction Targets**")

    target_df = pd.DataFrame({
        "Target": ["Scope 1+2 (−27.5%)", "Scope 3 (−27.5%)"],
        "Baseline\n2019": ["11.24M tCO₂e", "11.40M tCO₂e"],
        "Goal\n2030":     ["8.15M tCO₂e",  "8.26M tCO₂e"],
    })

    st.dataframe(
        target_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Market Cap Peers**")
    mc_display = mktcap_df[["Tick", "Name", "Market Capital", "Revenue (B)"]].copy()
    mc_display["Market Capital"] = mc_display["Market Capital"].apply(
        lambda x: f"${x/1e9:.1f}B" if pd.notna(x) else "—"
    )
    mc_display["Revenue (B)"] = mc_display["Revenue (B)"].apply(
        lambda x: f"${x:.2f}B" if pd.notna(x) else "—"
    )
    st.dataframe(mc_display, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# ROW 4: P2P DETAIL TABLE + HEATMAP
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">P2P DETAILED SCORES</div>', unsafe_allow_html=True)
col_tbl, col_heat = st.columns([1, 1.2])

with col_tbl:
    st.markdown("**Filtered Peer Score Table**")
    display_p2p = filtered_p2p[["Company", "Pilar", "Metric", "Score", "Peer Rank"]].copy()
    display_p2p["Company"] = display_p2p["Company"].map(lambda x: company_map.get(x, x))
    display_p2p["Score"] = display_p2p["Score"].round(2)
    st.dataframe(
        display_p2p.reset_index(drop=True),
        use_container_width=True,
        height=300,
    )

with col_heat:
    st.markdown("**ESG Score Heatmap — Company × Pillar**")

    # Only ESG-level rows
    heat_data = p2p_df[p2p_df["Pilar"] == "ESG"].copy()
    heat_pivot = heat_data.pivot_table(
        index="Metric", columns="Company", values="Score", aggfunc="mean"
    ).fillna(0)
    heat_pivot.columns = [company_map.get(c, c) for c in heat_pivot.columns]

    fig_heat = go.Figure(data=go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns.tolist(),
        y=heat_pivot.index.tolist(),
        colorscale=[
            [0.0, "#1a1a2e"],
            [0.3, "#16213e"],
            [0.6, "#0f3460"],
            [1.0, "#1e90ff"],
        ],
        text=np.round(heat_pivot.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=11, color="white"),
        hovertemplate="<b>%{x}</b><br>%{y}<br>Score: %{z:.2f}<extra></extra>",
        showscale=True,
        colorbar=dict(tickfont=dict(color="#8da9c4")),
    ))

    fig_heat.update_layout(
        paper_bgcolor="#162032",
        plot_bgcolor="#162032",
        xaxis=dict(tickfont=dict(color="#c0d8f0"), side="bottom"),
        yaxis=dict(tickfont=dict(color="#c0d8f0")),
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
    )
    st.plotly_chart(fig_heat, use_container_width=True)


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='color:#4a6278;font-size:11px;text-align:center;'>"
    "Data sourced from: Smurfit Westrock ESG Data Inventory · SW Carbon Footprint Calculator · "
    "SW P2P Review · GHG Protocol Framework · EY Assurance Schedule 2024 · "
    "MSCI / Sustainalytics / S&P Global ESG Ratings"
    "</p>",
    unsafe_allow_html=True,
)
