import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# -----------------------------
# ENHANCED COLOR SCHEME
# -----------------------------
BG = "#F5F0E6"  # Warm tan background
SIDEBAR_BG = "#E8DCC4"  # Light tan for sidebar
TEXT_DARK = "#3D2817"  # Dark brown text
TEXT_LIGHT = "#FFFFFF"  # White text
ACCENT_RED = "#B04223"  # Deep red
ACCENT_ORANGE = "#CC5500"  # Burnt orange
ACCENT_GOLD = "#BA994E"  # Gold/bronze
CARD_BG = "#FFF8E7"  # Cream card background
BORDER_COLOR = "#D4A574"  # Tan border

# KPI color coding
COLOR_EXCELLENT = "#2D7A3E"  # Green for excellent
COLOR_GOOD = "#BA994E"  # Gold for good
COLOR_WARNING = "#CC5500"  # Orange for warning
COLOR_CRITICAL = "#B04223"  # Red for critical

st.set_page_config(
    page_title="End-of-Month Processing Dashboard",
    layout="wide",
    page_icon="⛏️",
    initial_sidebar_state="expanded"
)

# -----------------------------
# CUSTOM CSS STYLING
# -----------------------------
st.markdown(f"""
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
    .material-icons {{
        font-family: 'Material Icons';
        font-weight: normal;
        font-style: normal;
        font-size: 20px;
        display: inline-block;
        line-height: 1;
        text-transform: none;
        letter-spacing: normal;
        word-wrap: normal;
        white-space: nowrap;
        direction: ltr;
        color: {ACCENT_RED};
        margin-right: 8px;
        vertical-align: middle;
    }}

    /* Main background */
    .stApp {{
        background-color: {BG};
    }}

    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background-color: {SIDEBAR_BG};
        border-right: 3px solid {BORDER_COLOR};
    }}

    [data-testid="stSidebar"] .stRadio > label {{
        color: {TEXT_DARK};
        font-size: 16px;
        font-weight: 600;
    }}

    /* Metric cards */
    .metric-card {{
        padding: 20px;
        background: linear-gradient(135deg, {ACCENT_GOLD} 0%, {ACCENT_ORANGE} 100%);
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 2px solid {BORDER_COLOR};
        transition: transform 0.2s;
    }}

    .metric-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }}

    /* Section headers */
    .section-header {{
        color: {ACCENT_RED};
        border-bottom: 4px solid {ACCENT_ORANGE};
        padding-bottom: 12px;
        margin-top: 30px;
        margin-bottom: 20px;
        font-weight: 700;
    }}

    /* Insight cards */
    .insight-card {{
        padding: 18px;
        background: {CARD_BG};
        border-radius: 10px;
        border-left: 5px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        margin-top: 10px;
        margin-bottom: 2px;
    }}

    /* Tables */
    .dataframe {{
        border: 2px solid {BORDER_COLOR} !important;
        border-radius: 8px;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {SIDEBAR_BG};
        border-radius: 8px;
        padding: 5px;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: {CARD_BG};
        border-radius: 6px;
        color: {TEXT_DARK};
        font-weight: 600;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {ACCENT_ORANGE};
        color: {TEXT_LIGHT};
    }}

    /* Custom caption styling */
    .caption-box {{
        background-color: {CARD_BG};
        padding: 10px;
        border-left: 4px solid {ACCENT_ORANGE};
        border-radius: 4px;
        margin-top: 10px;
        font-size: 14px;
        color: {TEXT_DARK};
    }}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# DATA LOADING & PROCESSING
# -----------------------------
@st.cache_data
def load_and_process_data():
    drill = pd.read_csv("drill.csv")
    comm = pd.read_csv("comm.csv")
    flot = pd.read_csv("flot.csv")

    # DRILLHOLES
    drill["Copper Equivalent (ppm)"] = (
            drill["cu_ppm"] + 150 * drill["au_ppm"] + 84 * drill["ag_ppm"]
    )
    drill["GradeCategory"] = pd.cut(
        drill["Copper Equivalent (ppm)"],
        bins=[-1, 1000, 2000, 1e9],
        labels=["Low", "Medium", "High"]
    )

    # COMMINUTION - Add mass simulation for realistic metrics
    comm["Average Thickness (mm)"] = (comm["th1"] + comm["th2"] + comm["th3"]) / 3
    comm["F80_P80"] = comm["F80"] / comm["P80"].replace(0, 1)
    comm["BondWorkMass"] = comm["A"] * comm["M"]
    
    # Simulate mass processed (tonnes) based on thickness
    np.random.seed(42)
    comm['mass_t'] = comm['Average Thickness (mm)'] * np.random.uniform(20, 50, size=len(comm))
    
    # Calculate copper potential in kg
    comm["Cu_potential_kg"] = comm["cu_ppm"] * comm["mass_t"] * 0.001
    comm["Energy_per_Cu"] = comm["BondWorkMass"] / comm["Cu_potential_kg"].replace(0, 1)
    comm["RecoveryPotential"] = comm["BondWorkMass"] * comm["cu_ppm"]

    # FLOTATION - Add mass simulation and actual recovery calculations
    np.random.seed(42)
    flot['feed_mass_t'] = np.random.uniform(1, 10, size=len(flot))
    
    # Calculate actual copper recovered in kg
    flot['cu_feed_kg'] = flot['cu_ppm'] * flot['feed_mass_t'] * 0.001
    flot['cu_recovered_kg'] = flot['cu_ppm'] * flot['feed_mass_t'] * flot['recovery_pct'] / 1000
    
    # Calculate recovery efficiency percentage
    flot['recovery_eff_pct'] = (flot['cu_recovered_kg'] / flot['cu_feed_kg'].replace(0, 1)) * 100
    flot["recovery_pct"] = flot["recovery_pct"] * 100
    
    # Enrichment ratio if concentrate grade exists
    if 'cu_ppm_conc' in flot.columns:
        flot['enrichment_ratio'] = flot['cu_ppm_conc'] / flot['cu_ppm'].replace(0, 1)
    
    # Keep legacy column for backward compatibility
    flot["RecoveredCu"] = flot['cu_recovered_kg']
    flot["Recovery_Efficiency"] = flot["recovery_pct"] / flot["xr"].replace(0, 1)

    return drill, comm, flot


drill, comm, flot = load_and_process_data()

# -----------------------------
# SIDEBAR NAVIGATION
# -----------------------------
st.sidebar.markdown(f"<h2 style='color:{ACCENT_RED};text-align:center;'>Navigation</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Initialize page if not set
if "page" not in st.session_state:
    st.session_state.page = "Executive Overview"

# Custom navigation buttons with HTML styling
st.sidebar.markdown(f"""
<style>
    .stButton > button {{
        background-color: {SIDEBAR_BG};
        color: {ACCENT_RED};
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        width: 100%;
        padding: 14px;
        margin: 10px 0;
    }}
    .stButton > button:hover {{
        background-color: {CARD_BG};
    }}
</style>
""", unsafe_allow_html=True)

if st.sidebar.button(":material/home: Executive Overview", use_container_width=True, key="btn_exec"):
    st.session_state.page = "Executive Overview"
    st.rerun()

if st.sidebar.button(":material/diamond: Resource Quality", use_container_width=True, key="btn_res"):
    st.session_state.page = "Resource Quality"
    st.rerun()

if st.sidebar.button(":material/manufacturing: Processing Performance", use_container_width=True, key="btn_proc"):
    st.session_state.page = "Processing Performance"
    st.rerun()

if st.sidebar.button(":material/add_chart: Download Report", use_container_width=True, key="btn_dl"):
    st.session_state.page = "Download Report"
    st.rerun()

st.sidebar.markdown("---")

# Get current page from session state
page = st.session_state.page

# -----------------------------
# REUSABLE PLOT CONFIGURATION
# -----------------------------
def configure_plot(fig, height=400):
    """Apply consistent styling to all plots"""
    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=height,
        font=dict(color=TEXT_DARK, family="Arial"),
        title_font=dict(size=16, color=ACCENT_RED, family="Arial Black"),
        margin=dict(t=60, b=30, l=50, r=50)
    )
    return fig


# Color maps for consistency
GRADE_COLORS = {"Low": "#FFE4B5", "Medium": "#FFA500", "High": "#CC5500"}
CONTINUOUS_ORANGES = px.colors.sequential.Oranges

# =============================
# PAGE 1: EXECUTIVE OVERVIEW
# =============================
if page == "Executive Overview":
    st.markdown(f"<h1 style='color:{ACCENT_RED};text-align:center;font-size:42px'>End-of-Month Processing Dashboard</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='text-align:center;color:{TEXT_DARK};font-size:20px;font-weight:500'>Monthly Performance Summary & Operational Insights</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # -----------------------------
    # TOP KPIs - FIRST ROW: GRADE METRICS
    # -----------------------------
    st.markdown(f"<h2 class='section-header'>Key Performance Indicators</h2>", unsafe_allow_html=True)

    # Calculate KPI values
    avg_cueq = drill['Copper Equivalent (ppm)'].mean()
    avg_cu = drill['cu_ppm'].mean()
    avg_au = drill['au_ppm'].mean()
    avg_ag = drill['ag_ppm'].mean()

    # FIRST ROW: Grade Metrics
    st.markdown(f"<h3 style='color:{ACCENT_ORANGE};margin-top:20px;margin-bottom:15px'>Resource Grade Metrics</h3>",
                unsafe_allow_html=True)

    kpis_row1 = [
        {
            "title": "Avg CuEq Grade",
            "value": f"{avg_cueq:.1f}",
            "unit": "ppm",
            "description": "Copper Equivalent",
            "icon": "",
            "status": "Excellent" if avg_cueq > 1500 else "Good" if avg_cueq > 1000 else "Monitor",
            "color": COLOR_EXCELLENT if avg_cueq > 1500 else COLOR_GOOD if avg_cueq > 1000 else COLOR_WARNING
        },
        {
            "title": "Avg Cu Grade",
            "value": f"{avg_cu:.1f}",
            "unit": "ppm",
            "description": "Copper Content",
            "icon": "",
            "status": "Excellent" if avg_cu > 1200 else "Good" if avg_cu > 800 else "Monitor",
            "color": COLOR_EXCELLENT if avg_cu > 1200 else COLOR_GOOD if avg_cu > 800 else COLOR_WARNING
        },
        {
            "title": "Avg Au Grade",
            "value": f"{avg_au:.2f}",
            "unit": "ppm",
            "description": "Gold Content",
            "icon": "",
            "status": "Excellent" if avg_au > 0.5 else "Good" if avg_au > 0.3 else "Monitor",
            "color": COLOR_EXCELLENT if avg_au > 0.5 else COLOR_GOOD if avg_au > 0.3 else COLOR_WARNING
        },
        {
            "title": "Avg Ag Grade",
            "value": f"{avg_ag:.2f}",
            "unit": "ppm",
            "description": "Silver Content",
            "icon": "",
            "status": "Excellent" if avg_ag > 10 else "Good" if avg_ag > 5 else "Monitor",
            "color": COLOR_EXCELLENT if avg_ag > 10 else COLOR_GOOD if avg_ag > 5 else COLOR_WARNING
        }
    ]

    kpi_cols_row1 = st.columns(4)
    for col, kpi in zip(kpi_cols_row1, kpis_row1):
        col.markdown(f"""
        <div class='insight-card' style='border-left-color:{kpi["color"]};background:{CARD_BG};min-height:180px'>
            <h4 style='color:{ACCENT_RED};margin:0;font-size:20px;text-align:center'>
                {kpi["title"]}
            </h4>
            <h2 style='margin:0px 0;font-size:32px;font-weight:bold;color:{TEXT_DARK};text-align:center'>
                {kpi["value"]}
            </h2>
            <p style='color:{TEXT_DARK};margin:0;font-size:12px;text-align:center;opacity:0.8'>
                {kpi["unit"]}
            </p>
            <p style='color:#666;margin:8px 0;font-size:11px;font-style:italic;text-align:center'>
                {kpi["description"]}
            </p>
            <div style='text-align:center;margin-top:12px'>
                <span style='background:{kpi["color"]};color:white;padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600'>
                    {kpi["status"]}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # SECOND ROW: Processing Performance Metrics
    st.markdown(
        f"<h3 style='color:{ACCENT_ORANGE};margin-top:20px;margin-bottom:15px'>Processing Performance Metrics</h3>",
        unsafe_allow_html=True)

    total_cu_recovered = flot['cu_recovered_kg'].sum()
    avg_recovery = flot['recovery_pct'].mean()
    avg_energy = comm['BondWorkMass'].mean()
    high_grade_count = (drill['GradeCategory'] == 'High').sum()
    high_grade_pct = (high_grade_count / len(drill)) * 100

    kpis_row2 = [
        {
            "title": "Total Cu Recovered",
            "value": f"{total_cu_recovered:.0f}",
            "unit": "kg",
            "description": "Revenue driver",
            "icon": "",
            "status": "Excellent" if total_cu_recovered > 50000 else "Good" if total_cu_recovered > 30000 else "Monitor",
            "color": COLOR_EXCELLENT if total_cu_recovered > 50000 else COLOR_GOOD if total_cu_recovered > 30000 else COLOR_WARNING
        },
        {
            "title": "Avg Recovery Rate",
            "value": f"{avg_recovery:.1f}",
            "unit": "%",
            "description": "Process efficiency",
            "icon": "",
            "status": "Excellent" if avg_recovery > 85 else "Good" if avg_recovery > 75 else "Review",
            "color": COLOR_EXCELLENT if avg_recovery > 85 else COLOR_GOOD if avg_recovery > 75 else COLOR_CRITICAL
        },
        {
            "title": "Avg Grinding Energy",
            "value": f"{avg_energy:.1f}",
            "unit": "kWh/t",
            "description": "Operating cost",
            "icon": "",
            "status": "Efficient" if avg_energy < 15 else "Monitor" if avg_energy < 20 else "High Cost",
            "color": COLOR_EXCELLENT if avg_energy < 15 else COLOR_WARNING if avg_energy < 20 else COLOR_CRITICAL
        },
        {
            "title": "High-Grade Samples",
            "value": f"{high_grade_count}",
            "unit": f"({high_grade_pct:.1f}%)",
            "description": "Mine planning",
            "icon": "",
            "status": "Excellent" if high_grade_pct > 25 else "Good" if high_grade_pct > 15 else "Limited",
            "color": COLOR_EXCELLENT if high_grade_pct > 25 else COLOR_GOOD if high_grade_pct > 15 else COLOR_WARNING
        }
    ]

    kpi_cols_row2 = st.columns(4)
    for col, kpi in zip(kpi_cols_row2, kpis_row2):
        col.markdown(f"""
        <div class='insight-card' style='border-left-color:{kpi["color"]};background:{CARD_BG};min-height:180px'>
            <div style='text-align:center;color:{ACCENT_RED};font-size:32px;margin-bottom:8px'>{kpi["icon"]}</div>
            <h4 style='color:{ACCENT_RED};margin:0;font-size:20px;text-align:center'>{kpi["title"]}</h4>
            <h2 style='margin:0px 0;font-size:32px;font-weight:bold;color:{TEXT_DARK};text-align:center'>{kpi["value"]}</h2>
            <p style='color:{TEXT_DARK};margin:0;font-size:12px;text-align:center;opacity:0.8'>{kpi["unit"]}</p>
            <p style='color:#666;margin:8px 0;font-size:11px;font-style:italic;text-align:center'>{kpi["description"]}</p>
            <div style='text-align:center;margin-top:12px'>
                <span style='background:{kpi["color"]};color:white;padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600'>
                    {kpi["status"]}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

# =============================
# PAGE 2: RESOURCE QUALITY
# =============================
elif page == "Resource Quality":
    st.markdown(f"<h1 style='color:{ACCENT_RED}'>Resource Quality Assessment</h1>", unsafe_allow_html=True)
    # st.markdown(
    #     f"<p style='color:{TEXT_DARK};font-size:16px'>Detailed analysis of drillhole data and ore body characteristics</p>",
    #     unsafe_allow_html=True)
    # st.markdown("---")

    # 3D Spatial Distribution
    st.markdown(f"<h2 class='section-header'>3D Ore Body Visualisation</h2>", unsafe_allow_html=True)

    fig_3d = px.scatter_3d(
        drill,
        x="X", y="Y", z="Z",
        color="Copper Equivalent (ppm)",
        size="cu_ppm",
        color_continuous_scale="oryel",
        title="<b>3D Spatial Distribution of Mineral Grades</b>",
        labels={
            "X": "X Coordinate (m)",
            "Y": "Y Coordinate (m)",
            "Z": "Depth (m)",
            "Copper Equivalent (ppm)": "CuEq (ppm)"
        }
    )

    fig_3d.update_traces(
        marker=dict(
            line=dict(
                width=0,
                color='DarkSlateGrey'
            )
        ),
        selector=dict(mode='markers')
    )

    # Configure with larger height and angled camera view to prevent cutoff
    fig_3d.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=550,
        font=dict(color=TEXT_DARK, family="Arial"),
        title_font=dict(size=16, color=ACCENT_RED, family="Arial Black"),
        margin=dict(t=50, b=30, l=30, r=30),
        scene=dict(
            xaxis=dict(backgroundcolor=CARD_BG, gridcolor="#D4A574"),
            yaxis=dict(backgroundcolor=CARD_BG, gridcolor="#D4A574"),
            zaxis=dict(backgroundcolor=CARD_BG, gridcolor="#D4A574"),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3),  # Angled upward view
                center=dict(x=0, y=0, z=-0.1)  # Slight downward center
            )
        )
    )
    st.plotly_chart(fig_3d, width='stretch')

    # Grade Metrics - Two charts in a row
    st.markdown(f"<h2 class='section-header'>Grade Metrics</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        fig_xy_cat = px.scatter(
            drill,
            x="X", y="Y",
            color="GradeCategory",
            title="<b>Plan View - Grade Categories</b>",
            labels={
                "X": "X Coordinate (m)",
                "Y": "Y Coordinate (m)",
                "GradeCategory": "Grade Category"
            },
            color_discrete_map=GRADE_COLORS,
            size_max=15
        )
        fig_xy_cat = configure_plot(fig_xy_cat, height=350)
        st.plotly_chart(fig_xy_cat, width='stretch')

    with col2:
        # Grade distribution pie chart
        grade_counts = drill["GradeCategory"].value_counts().reset_index()
        grade_counts.columns = ["Grade", "Count"]

        fig_pie = px.pie(
            grade_counts,
            values="Count",
            names="Grade",
            title="<b>Ore Grade Distribution</b>",
            color="Grade",
            color_discrete_map=GRADE_COLORS,
            hole=0.4
        )
        fig_pie = configure_plot(fig_pie, height=350)
        st.plotly_chart(fig_pie, width='stretch')

# =============================
# PAGE 3: PROCESSING PERFORMANCE
# =============================
elif page == "Processing Performance":
    st.markdown(f"<h1 style='color:{ACCENT_RED}'>Processing Performance Analysis</h1>", unsafe_allow_html=True)
    # st.markdown(f"<p style='color:{TEXT_DARK};font-size:15px;margin-bottom:20px;'>Comminution and flotation circuit efficiency metrics</p>",
    #             unsafe_allow_html=True)
    # st.markdown("---")

    # Compact process selection bar with horizontal layout
    st.markdown(f"""
    <style>
        /* Container for label and radio buttons */
        .process-selector-container {{
            background: {CARD_BG};
            border: 2px solid {ACCENT_ORANGE};
            border-radius: 4px;
            padding: 14px 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .process-selector-label {{
            font-size: 16px;
            font-weight: 600;
            color: {ACCENT_RED};
            letter-spacing: 0.3px;
            margin: 0;
            white-space: nowrap;
        }}
        
        /* Style the radio buttons to be inline */
        .process-radio {{
            flex: 1;
        }}
        
        .process-radio > div {{
            background: transparent !important;
            padding: 0 !important;
            border: none !important;
            box-shadow: none !important;
            display: flex !important;
            gap: 12px;
            justify-content: flex-start;
        }}
        
        .process-radio > div > label {{
            background: {SIDEBAR_BG};
            border: 1px solid {BORDER_COLOR};
            padding: 8px 24px !important;
            border-radius: 3px;
            font-size: 15px !important;
            font-weight: 600 !important;
            cursor: pointer;
            transition: all 0.2s;
            margin: 0 !important;
        }}
        
        .process-radio > div > label:hover {{
            background: {CARD_BG};
            border-color: {ACCENT_ORANGE};
        }}
        
        /* Hide the radio circle */
        .process-radio > div > label > div:first-child {{
            display: none !important;
        }}
    </style>
    
    <div class='process-selector-container'>
        <span class='process-selector-label'>Select Process Stage:</span>
        <div class='process-radio'>
    """, unsafe_allow_html=True)
    
    process_tab = st.radio(
        "",
        ["Comminution", "Flotation"],
        horizontal=True,
        label_visibility="collapsed",
        key="process_selector"
    )
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Clean up the process name
    # process_tab = process_tab.split(" ")[1]  # Remove emoji

    if process_tab == "Comminution":
        st.markdown(f"<h2 class='section-header'>Grinding & Size Reduction Performance</h2>", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
        # st.markdown(f"<p style='color:{TEXT_DARK};font-size:14px;margin-bottom:20px;'>Comminution circuit efficiency metrics</p>",
                    # unsafe_allow_html=True)

        # Comminution KPIs
        col1, col2, col3, col4 = st.columns(4)

        comm_metrics = [
            ("Avg Grinding Energy", f"{comm['BondWorkMass'].mean():.1f}", "kWh/t"),
            ("Avg Size Reduction", f"{comm['F80_P80'].mean():.1f}:1", "F80:P80"),
            ("Avg Thickness", f"{comm['Average Thickness (mm)'].mean():.1f}", "mm"),
            ("Max Cu Potential", f"{comm['Cu_potential_kg'].max():.0f}", "kg")
        ]

        for col, (label, value, unit) in zip([col1, col2, col3, col4], comm_metrics):
            col.markdown(f"""
            <div style='background:{ACCENT_GOLD};padding:18px;border-radius:3px;text-align:center;border:1px solid {BORDER_COLOR};box-shadow: 0 1px 2px rgba(0,0,0,0.08);'>
                <h4 style='color:{TEXT_LIGHT};margin:0;font-size:20px;font-weight:600;letter-spacing:0.2px;'>{label}</h4>
                <h2 style='color:{TEXT_LIGHT};margin:8px 0;font-size:32px;font-weight:700;'>{value}</h2>
                <p style='color:{TEXT_LIGHT};margin:0;font-size:15px;opacity:0.9;'>{unit}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts in a row
        col1, col2 = st.columns(2)

        with col1:
            fig_energy_grade = px.scatter(
                comm,
                x="cu_ppm",
                y="BondWorkMass",
                color="F80_P80",
                size="Average Thickness (mm)",
                title="<b>Grinding Energy vs Copper Grade</b>",
                labels={
                    "cu_ppm": "Copper Grade (ppm)",
                    "BondWorkMass": "Grinding Energy (kWh/t)",
                    "F80_P80": "Size Reduction Ratio (F80/P80)"
                },
                color_continuous_scale="oryel",
            )
            fig_energy_grade = configure_plot(fig_energy_grade, height=450)
            st.plotly_chart(fig_energy_grade, use_container_width=True)

        with col2:
            fig_energy_eff = px.scatter(
                comm,
                x="cu_ppm",
                y="Energy_per_Cu",
                color="F80_P80",
                title="<b>Energy Efficiency per Cu Unit</b>",
                labels={
                    "cu_ppm": "Copper Grade (ppm)",
                    "Energy_per_Cu": "Energy per Cu (kWh/t/ppm)",
                    "F80_P80": "Size Reduction Ratio (F80/P80)"
                },
                color_continuous_scale="oryel"
            )
            fig_energy_eff = configure_plot(fig_energy_eff, height=450)
            st.plotly_chart(fig_energy_eff, use_container_width=True)

    else:  # Flotation Circuit
        st.markdown(f"<h2 class='section-header'>Metal Recovery & Separation Performance</h2>", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
        # st.markdown(f"<p style='color:{TEXT_DARK};font-size:14px;margin-bottom:20px;'>Flotation circuit efficiency metrics</p>",
        #             unsafe_allow_html=True)

        # Flotation KPIs
        col1, col2, col3, col4 = st.columns(4)

        flot_metrics = [
            ("Avg Recovery Rate", f"{flot['recovery_pct'].mean():.1f}", "%"),
            ("Total Cu Recovered", f"{flot['cu_recovered_kg'].sum():.0f}", "kg"),
            ("Recovery Rate Std Dev", f"{flot['recovery_pct'].std():.1f}", "%"),
            ("Max Recovery Rate", f"{flot['recovery_pct'].max():.1f}", "%")
        ]

        for col, (label, value, unit) in zip([col1, col2, col3, col4], flot_metrics):
            col.markdown(f"""
            <div style='background:{ACCENT_GOLD};padding:18px;border-radius:3px;text-align:center;border:1px solid {BORDER_COLOR};box-shadow: 0 1px 2px rgba(0,0,0,0.08);'>
                <h4 style='color:{TEXT_LIGHT};margin:0;font-size:20px;font-weight:600;letter-spacing:0.2px;'>{label}</h4>
                <h2 style='color:{TEXT_LIGHT};margin:8px 0;font-size:32px;font-weight:700;'>{value}</h2>
                <p style='color:{TEXT_LIGHT};margin:0;font-size:15px;opacity:0.9;'>{unit}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Three charts side by side
        col1, col2, col3 = st.columns(3)

        with col1:
            fig_recovery_grade = px.scatter(
                flot,
                x="cu_ppm",
                y="recovery_pct",
                color="cu_recovered_kg",
                title="<b>Recovery Rate vs Feed Grade</b>",
                labels={
                    "cu_ppm": "Feed Copper Grade (ppm)",
                    "recovery_pct": "Recovery Rate (%)",
                    "cu_recovered_kg": "Recovered Cu (kg)"
                },
                color_continuous_scale="oryel"
            )
            fig_recovery_grade = configure_plot(fig_recovery_grade, height=450)
            st.plotly_chart(fig_recovery_grade, use_container_width=True)

        with col2:
            fig_recovered = px.scatter(
                flot,
                x="cu_ppm",
                y="cu_recovered_kg",
                color="recovery_pct",
                title="<b>Actual Copper Recovery</b>",
                labels={
                    "cu_ppm": "Feed Copper Grade (ppm)",
                    "cu_recovered_kg": "Recovered Cu (kg)",
                    "recovery_pct": "Recovery Rate (%)"
                },
                color_continuous_scale="oryel"
            )
            fig_recovered = configure_plot(fig_recovered, height=450)
            st.plotly_chart(fig_recovered, use_container_width=True)

        with col3:
            fig_grindability = px.scatter(
                flot,
                x="xr",
                y="recovery_pct",
                color="cu_ppm",
                title="<b>Recovery vs Grindability</b>",
                labels={
                    "xr": "Grindability Index (xr)",
                    "recovery_pct": "Recovery Rate (%)",
                    "cu_ppm": "Cu Grade (ppm)"
                },
                color_continuous_scale="oryel"
            )
            fig_grindability = configure_plot(fig_grindability, height=450)
            st.plotly_chart(fig_grindability, use_container_width=True)

# =============================
# PAGE 4: Download Report
# =============================
else:  # Download Report
    st.markdown(f"<h1 style='color:{ACCENT_RED}'>Download Report</h1>", unsafe_allow_html=True)
    # st.markdown(f"<p style='color:{TEXT_DARK};font-size:16px'>Export monthly summary report</p>",
    #             unsafe_allow_html=True)
    # st.markdown("---")

    # Monthly summary report
    # st.markdown("### Monthly Summary Report")
    st.markdown(f"<h2 class='section-header'>Monthly Summary Report</h2>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    summary_text = f"""
MONTHLY PROCESSING SUMMARY REPORT
================================

Period: Current Month
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

EXECUTIVE SUMMARY
-----------------
Total Drillholes Processed: {len(drill)}
High-Grade Ore Percentage: {(drill['GradeCategory'] == 'High').sum() / len(drill) * 100:.1f}%
Average Copper Equivalent: {drill['Copper Equivalent (ppm)'].mean():.1f} ppm
Average Copper Grade: {drill['cu_ppm'].mean():.1f} ppm
Average Gold Grade: {drill['au_ppm'].mean():.2f} ppm
Average Silver Grade: {drill['ag_ppm'].mean():.2f} ppm

COMMINUTION PERFORMANCE
-----------------------
Average Grinding Energy: {comm['BondWorkMass'].mean():.1f} kWh/t
Average Size Reduction (F80/P80): {comm['F80_P80'].mean():.2f}
Average Shell Thickness: {comm['Average Thickness (mm)'].mean():.1f} mm

FLOTATION PERFORMANCE
---------------------
Average Recovery Rate: {flot['recovery_pct'].mean():.1f}%
Total Copper Recovered: {flot['RecoveredCu'].sum():.0f} ppm·units
Samples with >90% Recovery: {(flot['recovery_pct'] > 90).sum()} ({(flot['recovery_pct'] > 90).sum() / len(flot) * 100:.1f}%)

TOP PERFORMERS
--------------
Best Drillhole (CuEq): {drill.loc[drill['Copper Equivalent (ppm)'].idxmax(), 'HOLEID']} - {drill['Copper Equivalent (ppm)'].max():.0f} ppm
Best Recovery: {flot.loc[flot['recovery_pct'].idxmax(), 'HOLEID']} - {flot['recovery_pct'].max():.1f}%
Highest Recovered Cu: {flot.loc[flot['RecoveredCu'].idxmax(), 'HOLEID']} - {flot['RecoveredCu'].max():.1f} ppm

OPERATIONAL INSIGHTS
-------------------
Resource Quality: {"Excellent" if (drill['GradeCategory'] == 'High').sum() / len(drill) * 100 > 25 else "Strong" if (drill['GradeCategory'] == 'High').sum() / len(drill) * 100 > 15 else "Moderate"}
Energy Efficiency: {"Efficient" if comm['BondWorkMass'].mean() < 15 else "Monitor" if comm['BondWorkMass'].mean() < 20 else "Review Required"}
Recovery Performance: {"Excellent" if (flot['recovery_pct'] > 90).sum() / len(flot) * 100 > 50 else "Good" if (flot['recovery_pct'] > 90).sum() / len(flot) * 100 > 30 else "Needs Attention"}

---
End of Report
"""

    st.text_area("Report Preview:", summary_text, height=400)

    st.download_button(
        label="Download Monthly Summary Report (TXT)",
        data=summary_text,
        file_name='monthly_summary_report.txt',
        mime='text/plain',
        width='stretch'
    )

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align:center;color:{TEXT_DARK};padding:20px'>
        <p style='font-size:14px;margin:0'>End-of-Month Processing Dashboard | Mineral Resource Management</p>
        <p style='font-size:12px;margin:5px 0;color:#999'>
            Data represents operational performance metrics for the current period
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
