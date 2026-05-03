# 🌍 Smurfit Westrock ESG Dashboard

A multi-page Streamlit dashboard for ESG analytics, carbon footprint tracking, and peer-to-peer review across the paper & packaging sector.

---

## 📁 Project Structure

```
sw-esg-dashboard/
│
├── app.py                          ← Main dashboard (Home page)
├── utils.py                        ← Shared data loaders, helpers, color maps
├── requirements.txt                ← Python dependencies
├── colab_runner.py                 ← Google Colab setup & localtunnel launcher
│
├── .streamlit/
│   └── config.toml                 ← Theme, server, and browser settings
│
├── pages/
│   ├── 1_📋_Data_Inventory.py      ← Deep-dive: ESG KPI inventory & quality scoring
│   ├── 2_🌱_Carbon_Footprint.py    ← Scope 1/2/3 trend, targets, intensity ratios
│   └── 3_🏆_P2P_Review.py         ← Peer-to-peer scoring, radar, heatmap, ranking
│
└── *.xlsx                          ← Your three Excel data files (place in root)
    ├── 05022026_SW_Data_Inventory.xlsx
    ├── SW_Carbon_Footprint.xlsx
    └── SW_P2P_Review.xlsx
```

---

## ⚙️ Setup — Local Machine

### 1. Prerequisites

- Python 3.9+ ([download](https://python.org))
- pip or conda

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Place your Excel files

Copy the three `.xlsx` files into the **same directory** as `app.py`:

| File | Description |
|------|-------------|
| `05022026_SW_Data_Inventory.xlsx` | ESG KPI inventory with quality scoring |
| `SW_Carbon_Footprint.xlsx` | GHG Protocol carbon footprint calculator |
| `SW_P2P_Review.xlsx` | Peer-to-peer ESG score comparison |

> ⚠️ **File names must match exactly** — the app reads them by name.

### 4. Run the dashboard

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## ☁️ Setup — Google Colab

Use `colab_runner.py` — it contains all four Colab cells as commented code blocks.

**Quick steps:**

1. Open a new Google Colab notebook
2. **Cell 1** — Install dependencies (`pip install`)
3. **Cell 2** — Upload your 3 Excel files via `files.upload()`
4. **Cell 3** — Write `app.py` to disk
5. **Cell 4** — Launch via `localtunnel` or `pyngrok`

The last cell prints a public URL like `https://xxxxx.loca.lt` — click it to access your live dashboard.

---

## 📊 Dashboard Pages

### 🏠 Home (`app.py`)
| Section | Content |
|---------|---------|
| KPI Cards | Total Value, Average Value, Record Count, SW ESG Score |
| Radar Chart | 8 sub-metrics compared across all 6 peers |
| Bar Chart | Total ESG score ranking by company |
| Line Chart | KPI trend by Business Unit & Year |
| 2024 Summary | KPI breakdown by category and business for latest year |
| Carbon Trend | Scope 1+2+3 actuals vs 2030 reduction target |
| Heatmap | Full ESG metric × company score matrix |

### 📋 Data Inventory (`pages/1_📋_Data_Inventory.py`)
- Pillar / Category / Business / Year filters + free-text KPI search
- Pie: KPI count by pillar
- Stacked bar: records by category & year
- Line trend: total value over time by category
- Grouped bar: latest-year breakdown by business & pillar
- Full searchable raw data table

### 🌱 Carbon Footprint (`pages/2_🌱_Carbon_Footprint.py`)
- Toggle between tCO₂e and MtCO₂e display
- Main trend chart with 2030 target overlay trajectories
- Scope 1/2/3 breakdown bar chart
- Carbon intensity trends (tCO₂e per $M revenue & per FTE)
- Reduction targets detail table

### 🏆 P2P Review (`pages/3_🏆_P2P_Review.py`)
- Company selector + pillar focus + company highlight
- Radar: 8 sub-metrics OR ESG pillar view
- Horizontal bar: company ranking
- Full score heatmap (metric × company)
- Searchable & color-coded detail table
- Market cap reference panel

---

## 🔧 Configuration

Edit `.streamlit/config.toml` to change:

```toml
[theme]
primaryColor = "#1e90ff"          # Accent / interactive color
backgroundColor = "#0e1117"       # Main background
secondaryBackgroundColor = "#162032"  # Cards / sidebar
textColor = "#e8f4fd"             # Body text

[server]
port = 8501                       # Change if 8501 is occupied
maxUploadSize = 200               # MB
```

---

## 🗂️ Data Architecture

### `utils.py` — Central Module

| Export | Type | Description |
|--------|------|-------------|
| `load_esg()` | `DataFrame` | ESG pivot sheet (all KPIs) |
| `load_inventory_scored()` | `DataFrame` | E/S/G/P scored rows concatenated |
| `load_p2p()` | `(DataFrame, DataFrame)` | P2P scores + market cap |
| `load_carbon_trend()` | `DataFrame` | 3-year emission totals |
| `load_carbon_targets()` | `DataFrame` | 2030 reduction targets |
| `COMPANY_MAP` | `dict` | Ticker → full name |
| `COMPANY_COLORS` | `dict` | Ticker → hex color |
| `BIZ_COLORS` | `dict` | Business unit → hex color |
| `PILLAR_COLORS` | `dict` | Pillar code → hex color |
| `dark_layout(**kwargs)` | `dict` | Base Plotly dark theme |
| `kpi_card(...)` | `str` | HTML KPI card component |
| `section_header(title)` | `None` | Renders a styled section header |
| `fmt_number(val)` | `str` | Auto K/M formatter |
| `peer_rank_color(rank)` | `str` | Rank → hex color |
| `build_trajectory(...)` | `DataFrame` | Linear reduction path |

All loaders use `@st.cache_data` — data is read once and reused across reruns.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `FileNotFoundError` for `.xlsx` | Ensure all 3 Excel files are in the same folder as `app.py` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `openpyxl` warnings about slicers | Safe to ignore — slicers are unsupported but data loads fine |
| Blank charts | Check sidebar filters — you may have deselected all options |
| Colab tunnel URL not appearing | Re-run Cell 4; localtunnel can be slow. Try the ngrok alternative in Cell 5 |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |

---

## 📦 Dependencies

| Package | Version | Use |
|---------|---------|-----|
| streamlit | ≥1.35 | Dashboard framework |
| pandas | ≥2.0 | Data manipulation |
| plotly | ≥5.20 | Interactive charts |
| openpyxl | ≥3.1.2 | Excel file reading |
| numpy | ≥1.26 | Numeric operations |
| xlrd | ≥2.0.1 | Legacy `.xls` support |
| Pillow | ≥10.0 | Image handling |

---

## 🏢 Data Sources

- **ESG Data Inventory**: Smurfit Westrock Sustainability Report 2024
- **Carbon Footprint**: GHG Protocol · EPA/DEFRA/IEA 2023 emission factors · EY Limited Assurance schedule
- **P2P Scores**: MSCI ESG Ratings · Sustainalytics Risk Score · S&P Global ESG Rank · Rep Risk Rating
- **Financial**: Market capitalisation & revenue as of assessment date

---

*Smurfit Westrock ESG Dashboard · Built with Streamlit & Plotly · May 2026*
