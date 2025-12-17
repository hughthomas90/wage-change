import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Salary Truth Checker", layout="wide")

st.title("💸 The Salary Realism Calculator (2020–2025)")
st.markdown("""
**The Brutal Reality Check:** This tool plots your salary against the Bank of England/ONS inflation data provided in your table.
It assumes you started in **2020** (getting no raise that first year) and tracks what happened to your purchasing power.
""")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("1. Personal Details")
start_salary = st.sidebar.number_input("Starting Salary in 2020 (£)", value=48000, step=1000)

st.sidebar.header("2. Company Adjustments (Footnotes)")
st.sidebar.markdown("Toggle these to see if the company's 'interventions' actually fixed the problem.")
apply_2022_adj = st.sidebar.checkbox("Apply 2022 Low Earner Adj?", value=True, help="Adds +1% if <50k, +2% if <30k (Footnote †)")
apply_2023_adj = st.sidebar.checkbox("Apply 2023 Cost of Living Adj?", value=True, help="Adds +2-3% based on salary (Footnote ‡)")
apply_2024_adj = st.sidebar.checkbox("Apply 2024 Variance?", value=True, help="Adds bump for lower earners similar to 2022 (Footnote §)")

# --- DATA ---
# Inflation from user table
inflation_map = {
    2020: 1.7, 2021: 1.0, 2022: 2.5, 2023: 8.8, 2024: 4.2, 2025: 3.9
}

# Base Pay Rises (Outstanding / Very Strong / Successful)
# Format: {Year: [Outstanding(1), Very Strong(2), Successful(3)]}
rates_db = {
    2020: [0.0, 0.0, 0.0],  # No raise in start year
    2021: [3.25, 2.75, 2.30],
    2022: [3.25, 2.75, 2.30], 
    2023: [3.70, 2.70, 2.30], 
    2024: [3.70, 2.70, 2.30], # Conservative mid-points
    2025: [3.70, 2.70, 2.30]
}

# --- CALCULATION ENGINE ---
def calculate_path(scenario_name):
    # Scenarios: 'Avg' (Always 3), 'Above' (Mixed), 'Top' (Always 1)
    
    current_salary = start_salary
    current_inflation_need = start_salary
    
    # Store history for plotting
    # We start recording at end of 2020
    history_salary = []
    history_inf = []
    history_years = [2020, 2021, 2022, 2023, 2024, 2025]
    
    # Tooltip data
    meta_raise_pct = []
    meta_inf_pct = []

    for year in history_years:
        # 1. INFLATION (Happens every year, including 2020)
        inf_rate = inflation_map[year]
        current_inflation_need = current_inflation_need * (1 + inf_rate / 100)
        meta_inf_pct.append(inf_rate)

        # 2. SALARY RAISE (Skipped in 2020)
        if year == 2020:
            actual_raise = 0.0
        else:
            # Determine Base Rate
            if scenario_name == 'Top Performer':
                idx = 0 # Outstanding
            elif scenario_name == 'Average Worker':
                idx = 2 # Successful
            else: # Above Average (Mixed: Avg early, Strong late)
                idx = 2 if year <= 2022 else 1
            
            base_rate = rates_db[year][idx]
            
            # Apply Footnotes (Logic based on *current* salary that year)
            adj = 0.0
            
            # 2022: +1% (30-50k), +2% (<30k)
            if year == 2022 and apply_2022_adj:
                if current_salary <= 30000: adj = 2.0
                elif current_salary <= 50000: adj = 1.0
            
            # 2023: +2.5% (<50k), +2% (>50k) - approx for "2-3%"
            if year == 2023 and apply_2023_adj:
                if current_salary <= 50000: adj = 2.5
                else: adj = 2.0
                
            # 2024: Similar to 2022
            if year == 2024 and apply_2024_adj:
                if current_salary <= 50000: adj = 1.5
                else: adj = 1.0

            actual_raise = base_rate + adj
            current_salary = current_salary * (1 + actual_raise / 100)
        
        meta_raise_pct.append(actual_raise)
        history_salary.append(current_salary)
        history_inf.append(current_inflation_need)

    return history_years, history_salary, history_inf, meta_raise_pct, meta_inf_pct

# Generate Data
y, sal_avg, inf_line, r_avg, i_meta = calculate_path('Average Worker')
_, sal_abv, _, r_abv, _ = calculate_path('Above Average')
_, sal_top, _, r_top, _ = calculate_path('Top Performer')

# --- PLOTTING ---
fig = go.Figure()

# Inflation Line (Red Dashed)
fig.add_trace(go.Scatter(
    x=y, y=inf_line,
    mode='lines+markers',
    name='Inflation (Stand Still)',
    line=dict(color='#e74c3c', width=4, dash='dot'),
    hovertemplate="<b>Year: %{x}</b><br>Required: £%{y:,.0f}<br>Inflation: %{customdata}%",
    customdata=i_meta
))

# Top Performer (Green)
fig.add_trace(go.Scatter(
    x=y, y=sal_top,
    mode='lines+markers',
    name='Outstanding (Top)',
    line=dict(color='#2ecc71', width=3),
    hovertemplate="<b>Year: %{x}</b><br>Salary: £%{y:,.0f}<br>Raise: %{customdata:.2f}%",
    customdata=r_top
))

# Above Average (Blue)
fig.add_trace(go.Scatter(
    x=y, y=sal_abv,
    mode='lines+markers',
    name='Above Average (Improving)',
    line=dict(color='#3498db', width=3),
    hovertemplate="<b>Year: %{x}</b><br>Salary: £%{y:,.0f}<br>Raise: %{customdata:.2f}%",
    customdata=r_abv
))

# Average (Yellow)
fig.add_trace(go.Scatter(
    x=y, y=sal_avg,
    mode='lines+markers',
    name='Average Worker',
    line=dict(color='#f1c40f', width=3),
    hovertemplate="<b>Year: %{x}</b><br>Salary: £%{y:,.0f}<br>Raise: %{customdata:.2f}%",
    customdata=r_avg
))

fig.update_layout(
    title="Cumulative Salary vs Cost of Living (Start 2020: No Raise Year 1)",
    xaxis_title="Year",
    yaxis_title="Salary (£)",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
)

st.plotly_chart(fig, use_container_width=True)

# --- METRICS ---
final_gap = sal_avg[-1] - inf_line[-1]
final_top_gap = sal_top[-1] - inf_line[-1]

c1, c2 = st.columns(2)
c1.metric("Inflation Requirement (2025)", f"£{int(inf_line[-1]):,}", f"+£{int(inf_line[-1]-start_salary):,} since 2020")
c2.metric("Avg Worker Salary (2025)", f"£{int(sal_avg[-1]):,}", f"{int(final_gap):,} gap", delta_color="inverse")

if final_top_gap < 0:
    st.error(f"⚠️ **Verdict:** Even an 'Outstanding' performer is poorer today than in 2020 (Gap: £{abs(int(final_top_gap)):,}).")
else:
    st.warning(f"⚠️ **Verdict:** Only 'Outstanding' performers kept up. Average workers lost £{abs(int(final_gap)):,}.")
