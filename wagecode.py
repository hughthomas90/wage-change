import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Salary vs RPI Analyzer", layout="wide")

st.title("💸 The RPI Reality Check (Year-to-March)")
st.markdown("""
This tool compares your salary against **RPI (Retail Prices Index)** for the year to March. 
RPI is the standard used by unions for pay negotiations because it better reflects housing costs (mortgages/rent).
""")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("1. Personal Details")
start_salary = st.sidebar.number_input("Starting Salary in March 2020 (£)", value=48000, step=1000)

st.sidebar.header("2. Inflation Metrics")
show_rpi = st.sidebar.checkbox("Show RPI (March) Line", value=True, help="Plots the Retail Prices Index. Usually higher than CPI.")
show_cpi = st.sidebar.checkbox("Show Company Table (ONS) Line", value=True, help="Plots the inflation figures provided in your original image.")

st.sidebar.header("3. Footnote Adjustments")
apply_2022_adj = st.sidebar.checkbox("Apply 2022 Low Earner Adj?", value=True)
apply_2023_adj = st.sidebar.checkbox("Apply 2023 Cost of Living Adj?", value=True)
apply_2024_adj = st.sidebar.checkbox("Apply 2024 Variance?", value=True)

# --- DATA ---
years = [2020, 2021, 2022, 2023, 2024, 2025]

# 1. User's Original Table Data (Likely CPI/CPIH Mix)
inf_table_map = {2020: 1.7, 2021: 1.0, 2022: 2.5, 2023: 8.8, 2024: 4.2, 2025: 3.9}

# 2. RPI Data (Official ONS "All Items" RPI percentage change over 12 months to March)
rpi_map = {
    2020: 2.6, 
    2021: 1.5, 
    2022: 9.0,   # The massive spike
    2023: 13.5,  # Peak crisis
    2024: 4.3, 
    2025: 3.2    # OBR Forecast / Current Estimate
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
    
    # We track two "Inflation Salaries" - one for Table Data, one for RPI
    curr_inf_table = start_salary
    curr_inf_rpi = start_salary
    
    history_salary = []
    history_inf_table = []
    history_inf_rpi = []
    
    # Tooltip data
    meta_raise = []
    meta_rpi = []
    meta_table = []

    for year in years:
        # 1. INFLATION (Happens every year)
        # Apply Table Inflation
        curr_inf_table *= (1 + inf_table_map[year] / 100)
        # Apply RPI Inflation
        curr_inf_rpi *= (1 + rpi_map[year] / 100)
        
        meta_table.append(inf_table_map[year])
        meta_rpi.append(rpi_map[year])

        # 2. SALARY (Skipped in 2020)
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
        history_salary.append(current_salary)
        history_inf_table.append(curr_inf_table)
        history_inf_rpi.append(curr_inf_rpi)

    return history_salary, history_inf_table, history_inf_rpi, meta_raise, meta_rpi, meta_table

# Generate Data
sal_avg, inf_tab, inf_rpi, r_avg, m_rpi, m_tab = calculate_path('Average Worker')
sal_abv, _, _, r_abv, _, _ = calculate_path('Above Average')
sal_top, _, _, r_top, _, _ = calculate_path('Top Performer')

# --- PLOTTING ---
fig = go.Figure()

# RPI Line (Purple)
if show_rpi:
    fig.add_trace(go.Scatter(
        x=years, y=inf_rpi,
        mode='lines+markers',
        name='RPI (Union Standard)',
        line=dict(color='#8e44ad', width=4, dash='dot'),
        hovertemplate="<b>Year: %{x}</b><br>Needs: £%{y:,.0f}<br>RPI: %{customdata}%",
        customdata=m_rpi
    ))

# Table Inflation Line (Red)
if show_cpi:
    fig.add_trace(go.Scatter(
        x=years, y=inf_tab,
        mode='lines+markers',
        name='Company Table (CPI)',
        line=dict(color='#e74c3c', width=2, dash='dash'),
        hovertemplate="<b>Year: %{x}</b><br>Needs: £%{y:,.0f}<br>Table Inf: %{customdata}%",
        customdata=m_tab
    ))

# Salary Lines
fig.add_trace(go.Scatter(
    x=years, y=sal_top, name='Outstanding (Top)',
    line=dict(color='#2ecc71', width=3),
    hovertemplate="Salary: £%{y:,.0f} (Raise: %{customdata:.2f}%)", customdata=r_top
))

fig.add_trace(go.Scatter(
    x=years, y=sal_abv, name='Above Average',
    line=dict(color='#3498db', width=3),
    hovertemplate="Salary: £%{y:,.0f} (Raise: %{customdata:.2f}%)", customdata=r_abv
))

fig.add_trace(go.Scatter(
    x=years, y=sal_avg, name='Average Worker',
    line=dict(color='#f1c40f', width=3),
    hovertemplate="Salary: £%{y:,.0f} (Raise: %{customdata:.2f}%)", customdata=r_avg
))

fig.update_layout(
    title="Salary vs RPI (The Real Cost of Living)",
    xaxis_title="Year", yaxis_title="Salary (£)",
    hovermode="x unified", template="plotly_white",
    legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
)

st.plotly_chart(fig, use_container_width=True)

# --- ANALYSIS ---
gap_rpi = sal_avg[-1] - inf_rpi[-1]
gap_top_rpi = sal_top[-1] - inf_rpi[-1]
rpi_req = inf_rpi[-1]

st.markdown("### 📉 The Verdict")
col1, col2, col3 = st.columns(3)
col1.metric("Required for RPI", f"£{int(rpi_req):,}", f"Cost of Living")
col2.metric("Avg Worker Salary", f"£{int(sal_avg[-1]):,}", f"{int(gap_rpi):,} deficit", delta_color="inverse")
col3.metric("Top Performer Gap", f"{int(gap_top_rpi):,}", "Even the best are losing", delta_color="inverse")

if gap_rpi < 0:
    st.error(f"⚠️ **Conclusion:** An Average Worker is **£{abs(int(gap_rpi)):,}** worse off than in 2020 when adjusted for RPI.")
