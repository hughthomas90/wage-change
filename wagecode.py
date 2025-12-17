import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Salary vs. Inflation Analyzer", layout="wide")

st.title("💸 Detailed Salary vs. Inflation Analyzer (2020-2025)")
st.markdown("""
This tool models your base salary progression starting from **2020**. 
It automatically applies the **'Cost of Living' footnotes** from your table (e.g., extra % for earners under £50k) 
based on what your salary is in that specific year.
""")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Configuration")
start_salary = st.sidebar.number_input("Starting Salary in 2020 (£)", value=40000, step=1000)

# Toggle for the specific footnote logic
apply_col_adj = st.sidebar.checkbox("Apply 'Lower Earner' Adjustments?", value=True, 
    help="If checked, adds the extra percentages mentioned in footnotes for 2022, 2023, and 2024 if salary is under threshold.")

# --- DATA DEFINITIONS ---
years = [2020, 2021, 2022, 2023, 2024, 2025]

# Base Rates from Table (Outstanding / Very Strong / Successful)
# Note: 2020 is start year (no raise). Raises apply to 2021, 2022, etc.
# Format: {Year: [Outstanding, Very Strong, Successful]}
rates_db = {
    2021: [3.25, 2.75, 2.30],
    2022: [3.25, 2.75, 2.30], # Base rates before footnote
    2023: [3.70, 2.70, 2.30], # Base rates before footnote
    2024: [3.70, 2.70, 2.30], # Midpoints of ranges (2.7-4.7, etc) -> using conservative mid-low
    2025: [3.70, 2.70, 2.30]
}

# Inflation (ONS) from table
inflation_map = {
    2020: 1.7, 2021: 1.0, 2022: 2.5, 2023: 8.8, 2024: 4.2, 2025: 3.9
}

# --- CALCULATION LOGIC ---

def calculate_salary_path(mode):
    # Mode: 'avg' (3), 'above' (mix), 'top' (1)
    salary = start_salary
    salary_history = [salary]
    inflation_salary = start_salary
    inflation_history = [inflation_salary]
    
    # Metadata for tooltips
    meta_raises = [0.0] 
    meta_inf = [inflation_map[2020]]

    # Logic: Start 2020. 
    # Loop 2021 -> 2025
    for year in years[1:]:
        # 1. Determine Performance Rating
        if mode == 'top':
            rating_idx = 0 # Outstanding
        elif mode == 'avg':
            rating_idx = 2 # Successful
        else: # Above Average (Mixed)
            # Logic: Average in 2021/2022, Strong in 2023/24/25
            rating_idx = 2 if year <= 2022 else 1
            
        base_raise = rates_db[year][rating_idx]
        
        # 2. Apply Footnote Adjustments (The "Options" logic)
        adjustment = 0.0
        if apply_col_adj:
            # 2022 Footnote: +1% if 30-50k, +2% if <30k
            if year == 2022:
                if salary <= 30000: adjustment = 2.0
                elif salary <= 50000: adjustment = 1.0
            
            # 2023 Footnote: "Plus 2-3%" (Modeling as +2.5% for <50k, +2% otherwise)
            elif year == 2023:
                if salary <= 50000: adjustment = 2.5
                else: adjustment = 2.0
            
            # 2024 Footnote: "Similar to 2022-23" (Modeling as +1.5% for <50k)
            elif year == 2024:
                if salary <= 50000: adjustment = 1.5
                else: adjustment = 1.0

        total_raise = base_raise + adjustment
        
        # 3. Update Salary
        salary = salary * (1 + total_raise / 100)
        salary_history.append(salary)
        meta_raises.append(total_raise)
        
        # 4. Update Inflation (The "Stand Still" line)
        # We apply the inflation of the *current* year to show what you need at end of year
        inf_rate = inflation_map[year]
        inflation_salary = inflation_salary * (1 + inf_rate / 100)
        inflation_history.append(inflation_salary)
        meta_inf.append(inf_rate)

    return salary_history, inflation_history, meta_raises, meta_inf

# Run Calcs
sal_avg, inf_avg, r_avg, i_avg = calculate_salary_path('avg')
sal_abv, _, r_abv, _ = calculate_salary_path('above')
sal_top, _, r_top, _ = calculate_salary_path('top')

# --- PLOTTING WITH PLOTLY ---
fig = go.Figure()

# 1. Inflation Line (The Baseline)
fig.add_trace(go.Scatter(
    x=years, y=inf_avg,
    mode='lines+markers',
    name='Inflation (Stand Still)',
    line=dict(color='red', width=4, dash='dot'),
    hovertemplate="<b>Year: %{x}</b><br>Req. Salary: £%{y:,.0f}<br>Inflation: %{customdata}%",
    customdata=i_avg
))

# 2. Top Performer
fig.add_trace(go.Scatter(
    x=years, y=sal_top,
    mode='lines+markers',
    name='Outstanding Performer',
    line=dict(color='#2ecc71', width=3),
    hovertemplate="<b>Year: %{x}</b><br>Salary: £%{y:,.0f}<br>Raise: %{customdata:.2f}%",
    customdata=r_top
))

# 3. Above Average
fig.add_trace(go.Scatter(
    x=years, y=sal_abv,
    mode='lines+markers',
    name='Above Avg (Improving)',
    line=dict(color='#3498db', width=3),
    hovertemplate="<b>Year: %{x}</b><br>Salary: £%{y:,.0f}<br>Raise: %{customdata:.2f}%",
    customdata=r_abv
))

# 4. Average
fig.add_trace(go.Scatter(
    x=years, y=sal_avg,
    mode='lines+markers',
    name='Average Worker',
    line=dict(color='#f1c40f', width=3),
    hovertemplate="<b>Year: %{x}</b><br>Salary: £%{y:,.0f}<br>Raise: %{customdata:.2f}%",
    customdata=r_avg
))

# Layout Styling
fig.update_layout(
    title="Salary Progression vs. Inflation (Mouse over points for details)",
    xaxis_title="Year",
    yaxis_title="Base Salary (£)",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- ANALYSIS TEXT ---
final_gap = sal_avg[-1] - inf_avg[-1]
st.markdown("### 📊 The Verdict")

if final_gap < 0:
    st.error(f"""
    **Result:** An Average Worker is **£{abs(int(final_gap)):,} poorer** in real terms than in 2020.
    
    Even with the footnote adjustments (extra % for cost of living), the massive inflation in 2023 (8.8%) 
    wiped out the gains. 
    """)
else:
    st.success("The salary has kept up with inflation!")

st.markdown("---")
st.caption("Note: Inflation data uses the ONS figures provided in your table. 'Above Average' assumes Successful performance in 2021/22 and Very Strong in 2023/24/25.")
