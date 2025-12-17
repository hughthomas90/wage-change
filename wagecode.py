import streamlit as st
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Salary vs Inflation Analysis", layout="wide")

st.title("Salary vs Inflation Analysis (2020–2025)")
st.markdown("""
This tool compares salary progression against different inflation indices.
* **CPIH (Provided Data):** Based on the table provided in the input.
* **CPI (Official ONS):** Consumer Prices Index (Year to March).
* **RPI (Official ONS):** Retail Prices Index (Year to March).
""")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Configuration")
start_salary = st.sidebar.number_input("Starting Salary in 2020 (£)", value=40000, step=1000)

st.sidebar.header("Inflation Indices")
show_cpih = st.sidebar.checkbox("Show CPIH (Provided Data)", value=True)
show_cpi = st.sidebar.checkbox("Show CPI (Official ONS)", value=True)
show_rpi = st.sidebar.checkbox("Show RPI (Official ONS)", value=True)

st.sidebar.header("Footnote Adjustments")
apply_2022_adj = st.sidebar.checkbox("2022: Low Earner Adjustment", value=True, help="Adds +1% if salary <50k, +2% if <30k")
apply_2023_adj = st.sidebar.checkbox("2023: Cost of Living Adjustment", value=True, help="Adds +2-3% based on salary tiers")
apply_2024_adj = st.sidebar.checkbox("2024: Variance Adjustment", value=True, help="Adds bump for lower earners")

# --- DATA ---
years = [2020, 2021, 2022, 2023, 2024, 2025]

# Inflation Data (Percentage Change Year-on-Year)
# Note: 2020 is the base year, so inflation figures apply to 2021 onwards.
inflation_data = {
    # From provided table
    'CPIH': {2021: 1.0, 2022: 2.5, 2023: 8.8, 2024: 4.2, 2025: 3.9},
    # ONS Official (Year to March)
    'CPI': {2021: 0.7, 2022: 7.0, 2023: 10.1, 2024: 3.2, 2025: 2.6},
    'RPI': {2021: 1.5, 2022: 9.0, 2023: 13.5, 2024: 4.3, 2025: 3.2}
}

# Salary Performance Rates (Outstanding / Very Strong / Successful)
# Format: {Year: [Outstanding(1), Very Strong(2), Successful(3)]}
# 2020 is base, raises apply in 2021
pay_rates = {
    2021: [3.25, 2.75, 2.30],
    2022: [3.25, 2.75, 2.30], 
    2023: [3.70, 2.70, 2.30], 
    2024: [3.70, 2.70, 2.30],
    2025: [3.70, 2.70, 2.30]
}

# --- CALCULATION LOGIC ---
def calculate_trajectory(mode):
    # Modes: 'avg', 'above', 'top', 'cpih', 'cpi', 'rpi'
    
    # Initialize all paths at the exact same starting salary in 2020
    trajectory = [start_salary]
    current_val = start_salary
    
    # Tooltip metadata
    meta_changes = [0.0] 

    for i in range(1, len(years)):
        year = years[i]
        pct_change = 0.0
        
        # Logic for Salary Lines
        if mode in ['avg', 'above', 'top']:
            # Determine Base Rate
            if mode == 'top': idx = 0 
            elif mode == 'avg': idx = 2 
            else: idx = 2 if year <= 2022 else 1 # Average early, Strong late
            
            base = pay_rates[year][idx]
            
            # Apply Footnotes
            adj = 0.0
            if year == 2022 and apply_2022_adj:
                if current_val <= 30000: adj = 2.0
                elif current_val <= 50000: adj = 1.0
            
            if year == 2023 and apply_2023_adj:
                if current_val <= 50000: adj = 2.5
                else: adj = 2.0
                
            if year == 2024 and apply_2024_adj:
                if current_val <= 50000: adj = 1.5
                else: adj = 1.0
            
            pct_change = base + adj
            
        # Logic for Inflation Lines
        elif mode == 'cpih':
            pct_change = inflation_data['CPIH'][year]
        elif mode == 'cpi':
            pct_change = inflation_data['CPI'][year]
        elif mode == 'rpi':
            pct_change = inflation_data['RPI'][year]
            
        # Apply change
        current_val = current_val * (1 + pct_change / 100)
        trajectory.append(current_val)
        meta_changes.append(pct_change)
        
    return trajectory, meta_changes

# Compute Trajectories
sal_avg, m_avg = calculate_trajectory('avg')
sal_abv, m_abv = calculate_trajectory('above')
sal_top, m_top = calculate_trajectory('top')

inf_cpih, m_cpih = calculate_trajectory('cpih')
inf_cpi, m_cpi = calculate_trajectory('cpi')
inf_rpi, m_rpi = calculate_trajectory('rpi')

# --- PLOTTING ---
fig = go.Figure()

# 1. Inflation Lines (Dashed)
if show_rpi:
    fig.add_trace(go.Scatter(
        x=years, y=inf_rpi, name='RPI (Official)',
        mode='lines+markers',
        line=dict(color='#8e44ad', width=3, dash='dot'),
        hovertemplate="£%{y:,.0f} (+%{customdata}%)", customdata=m_rpi
    ))

if show_cpi:
    fig.add_trace(go.Scatter(
        x=years, y=inf_cpi, name='CPI (Official)',
        mode='lines+markers',
        line=dict(color='#2980b9', width=3, dash='dash'),
        hovertemplate="£%{y:,.0f} (+%{customdata}%)", customdata=m_cpi
    ))

if show_cpih:
    fig.add_trace(go.Scatter(
        x=years, y=inf_cpih, name='CPIH (Provided Data)',
        mode='lines+markers',
        line=dict(color='#c0392b', width=3, dash='dash'),
        hovertemplate="£%{y:,.0f} (+%{customdata}%)", customdata=m_cpih
    ))

# 2. Salary Lines (Solid)
fig.add_trace(go.Scatter(
    x=years, y=sal_top, name='Outstanding Performance',
    mode='lines+markers',
    line=dict(color='#27ae60', width=3),
    hovertemplate="£%{y:,.0f} (+%{customdata:.2f}%)", customdata=m_top
))

fig.add_trace(go.Scatter(
    x=years, y=sal_abv, name='Above Average',
    mode='lines+markers',
    line=dict(color='#2980b9', width=3), # Different blue/solid
    hovertemplate="£%{y:,.0f} (+%{customdata:.2f}%)", customdata=m_abv
))

fig.add_trace(go.Scatter(
    x=years, y=sal_avg, name='Average Performance',
    mode='lines+markers',
    line=dict(color='#f39c12', width=3),
    hovertemplate="£%{y:,.0f} (+%{customdata:.2f}%)", customdata=m_avg
))

fig.update_layout(
    title="Salary vs Inflation (Base Year 2020)",
    xaxis_title="Year",
    yaxis_title="Salary Value (£)",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
)

st.plotly_chart(fig, use_container_width=True)

# --- SUMMARY METRICS ---
st.markdown("### Summary Statistics (2025)")

col1, col2, col3 = st.columns(3)
col1.metric("CPIH Projection (Provided)", f"£{int(inf_cpih[-1]):,}")
col2.metric("Actual Average Salary", f"£{int(sal_avg[-1]):,}")
col3.metric("Difference", f"{int(sal_avg[-1] - inf_cpih[-1]):,}", delta_color="normal")

st.markdown("---")
st.caption("Note: All trajectories start at the same base salary in 2020. Adjustments for lower earners/cost of living are applied in 2022, 2023, and 2024 as per footnotes.")
