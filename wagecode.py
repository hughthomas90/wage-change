import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Salary Negotiation Master", layout="wide")

st.title("💸 The Salary Reality Check: CPI vs RPI vs Company")
st.markdown("""
**Choose your truth:**
* **Company Line:** The inflation figures used to justify your pay (likely CPIH or cherry-picked).
* **CPI (Blue):** Best if you **rent** or own outright. Tracks goods/services but excludes owner-occupier housing.
* **RPI (Purple):** Best if you have a **mortgage**. Tracks the real cost of debt and housing.
""")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("1. Personal Details")
start_salary = st.sidebar.number_input("Starting Salary in March 2020 (£)", value=48000, step=1000)

st.sidebar.header("2. Choose Your Inflation")
show_cpi = st.sidebar.checkbox("Show CPI (Renters/No Mortgage)", value=True, help="Consumer Prices Index (March). Best for pure cost of living.")
show_rpi = st.sidebar.checkbox("Show RPI (Mortgage Holders)", value=True, help="Retail Prices Index (March). Includes housing interest.")
show_table = st.sidebar.checkbox("Show Company Table (The Justification)", value=True, help="The numbers from your image.")

st.sidebar.header("3. Footnote Adjustments")
apply_2022_adj = st.sidebar.checkbox("Apply 2022 Low Earner Adj?", value=True)
apply_2023_adj = st.sidebar.checkbox("Apply 2023 Cost of Living Adj?", value=True)
apply_2024_adj = st.sidebar.checkbox("Apply 2024 Variance?", value=True)

# --- DATA SOURCE: ONS March Figures ---
years = [2020, 2021, 2022, 2023, 2024, 2025]

# 1. Company Table (From your image)
inf_table_map = {2020: 1.7, 2021: 1.0, 2022: 2.5, 2023: 8.8, 2024: 4.2, 2025: 3.9}

# 2. RPI (ONS Series: CZBH - Percentage change over 12 months, March)
# Source: https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/czbh/mm23
rpi_map = {
    2020: 2.6, 
    2021: 1.5, 
    2022: 9.0,   # Massive divergence starts here
    2023: 13.5,  # The crisis peak
    2024: 4.3, 
    2025: 3.2    # Estimate/Forecast
}

# 3. CPI (ONS Series: D7G7 - Percentage change over 12 months, March)
# Source: https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23
cpi_map = {
    2020: 1.5,
    2021: 0.7,
    2022: 7.0,   # Note: Company used 2.5% vs Real 7.0%
    2023: 10.1,  # Note: Company used 8.8% vs Real 10.1%
    2024: 3.2,
    2025: 2.6    # OBR Forecast
}

# Base Pay Rises
rates_db = {
    2020: [0.0, 0.0, 0.0],
    2021: [3.25, 2.75, 2.30],
    2022: [3.25, 2.75, 2.30], 
    2023: [3.70, 2.70, 2.30], 
    2024: [3.70, 2.70, 2.30],
    2025: [3.70, 2.70, 2.30]
}

# --- CALCULATION ENGINE ---
def calculate_path(scenario_name):
    current_salary = start_salary
    
    # Track 3 inflation paths
    curr_inf_table = start_salary
    curr_inf_rpi = start_salary
    curr_inf_cpi = start_salary
    
    hist_sal = []
    hist_inf_tab = []
    hist_inf_rpi = []
    hist_inf_cpi = []
    
    # Metadata for tooltips
    meta_raise = []
    meta_rpi = []
    meta_cpi = []
    meta_tab = []

    for year in years:
        # 1. APPLY INFLATION (March Data)
        curr_inf_table *= (1 + inf_table_map[year] / 100)
        curr_inf_rpi *= (1 + rpi_map[year] / 100)
        curr_inf_cpi *= (1 + cpi_map[year] / 100)
        
        meta_tab.append(inf_table_map[year])
        meta_rpi.append(rpi_map[year])
        meta_cpi.append(cpi_map[year])

        # 2. APPLY SALARY (Skipped in 2020)
        if year == 2020:
            actual_raise = 0.0
        else:
            # Determine Base Rate
            if scenario_name == 'Top Performer': idx = 0 
            elif scenario_name == 'Average Worker': idx = 2 
            else: idx = 2 if year <= 2022 else 1 # Above Avg
            
            base_rate = rates_db[year][idx]
            
            # Adjustments
            adj = 0.0
            if year == 2022 and apply_2022_adj:
                if current_salary <= 30000: adj = 2.0
                elif current_salary <= 50000: adj = 1.0
            if year == 2023 and apply_2023_adj:
                if current_salary <= 50000: adj = 2.5
                else: adj = 2.0
            if year == 2024 and apply_2024_adj:
                if current_salary <= 50000: adj = 1.5
                else: adj = 1.0

            actual_raise = base_rate + adj
            current_salary *= (1 + actual_raise / 100)
        
        meta_raise.append(actual_raise)
        hist_sal.append(current_salary)
        hist_inf_tab.append(curr_inf_table)
        hist_inf_rpi.append(curr_inf_rpi)
        hist_inf_cpi.append(curr_inf_cpi)

    return hist_sal, hist_inf_tab, hist_inf_rpi, hist_inf_cpi, meta_raise, meta_rpi, meta_cpi, meta_tab

# Run Calculations
sal_avg, inf_tab, inf_rpi, inf_cpi, r_avg, m_rpi, m_cpi, m_tab = calculate_path('Average Worker')
sal_abv, _, _, _, r_abv, _, _, _ = calculate_path('Above Average')
sal_top, _, _, _, r_top, _, _, _ = calculate_path('Top Performer')

# --- PLOTTING ---
fig = go.Figure()

# 1. RPI (Purple)
if show_rpi:
    fig.add_trace(go.Scatter(
        x=years, y=inf_rpi, mode='lines+markers', name='RPI (Mortgages)',
        line=dict(color='#8e44ad', width=4, dash='dot'),
        hovertemplate="<b>%{x}</b><br>Need: £%{y:,.0f}<br>RPI: %{customdata}%", customdata=m_rpi
    ))

# 2. CPI (Blue)
if show_cpi:
    fig.add_trace(go.Scatter(
        x=years, y=inf_cpi, mode='lines+markers', name='CPI (Rent/Living)',
        line=dict(color='#2980b9', width=4, dash='dash'),
        hovertemplate="<b>%{x}</b><br>Need: £%{y:,.0f}<br>CPI: %{customdata}%", customdata=m_cpi
    ))

# 3. Company Table (Red)
if show_table:
    fig.add_trace(go.Scatter(
        x=years, y=inf_tab, mode='lines+markers', name='Company Table',
        line=dict(color='#e74c3c', width=2),
        hovertemplate="<b>%{x}</b><br>Need: £%{y:,.0f}<br>Table: %{customdata}%", customdata=m_tab
    ))

# 4. Salary Lines
fig.add_trace(go.Scatter(
    x=years, y=sal_top, name='Outstanding Perf.',
    line=dict(color='#2ecc71', width=3),
    hovertemplate="£%{y:,.0f} (Rise: %{customdata:.2f}%)", customdata=r_top
))
fig.add_trace(go.Scatter(
    x=years, y=sal_avg, name='Avg Worker',
    line=dict(color='#f1c40f', width=3),
    hovertemplate="£%{y:,.0f} (Rise: %{customdata:.2f}%)", customdata=r_avg
))

fig.update_layout(
    title="Cumulative Salary vs Inflation Metrics (2020-2025)",
    xaxis_title="Year", yaxis_title="Salary (£)",
    hovermode="x unified", template="plotly_white",
    legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
)

st.plotly_chart(fig, use_container_width=True)

# --- ANALYSIS SECTION ---
st.markdown("### 📊 The Deficit Analysis (2025)")

# Calculate gaps
gap_cpi = sal_avg[-1] - inf_cpi[-1]
gap_rpi = sal_avg[-1] - inf_rpi[-1]

c1, c2, c3 = st.columns(3)
c1.metric("CPI Need (Renters)", f"£{int(inf_cpi[-1]):,}")
c2.metric("RPI Need (Mortgages)", f"£{int(inf_rpi[-1]):,}")
c3.metric("Your Salary (Avg)", f"£{int(sal_avg[-1]):,}")

st.markdown("---")

if gap_cpi < 0:
    st.error(f"""
    **If you rent/own outright:** You are **£{abs(int(gap_cpi)):,}** poorer than in 2020.
    The company under-matched CPI in 2022 (2.5% vs 7.0%) and 2023 (8.8% vs 10.1%).
    """)

if gap_rpi < 0:
    st.error(f"""
    **If you have a mortgage:** You are **£{abs(int(gap_rpi)):,}** poorer than in 2020.
    RPI peaked at 13.5% in 2023, but you likely received a raise of ~5%.
    """)

st.caption("Sources: ONS Consumer Price Inflation (Series D7G7 for CPI, CZBH for RPI) - March of each year.")
