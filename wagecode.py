import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Salary vs Inflation Analysis", layout="wide")

st.title("Salary vs Inflation Analysis (2020–2025)")
st.markdown("""
This tool compares salary progression against different inflation indices.
* **CPIH:** Consumer Prices Index including owner occupiers' housing costs (Year to March).
* **CPI:** Consumer Prices Index (Year to March).
* **RPI:** Retail Prices Index (Year to March).
""")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Configuration")
start_salary = st.sidebar.number_input("Starting Salary in 2020 (£)", value=40000, step=1000)

st.sidebar.header("Main Graph Settings")
show_cpih = st.sidebar.checkbox(
    "Show CPIH Trajectory", 
    value=True,
    help="**Consumer Prices Index including owner occupiers' housing costs (CPIH)**\n\n**How it works:** The most comprehensive measure. It tracks the change in prices for a basket of goods and services, explicitly INCLUDING costs associated with owning, maintaining, and living in one's own home.\n\n**Who it is for:** Homeowners and those wanting the most accurate picture of total living costs."
)
show_cpi = st.sidebar.checkbox(
    "Show CPI Trajectory", 
    value=True,
    help="**Consumer Prices Index (CPI)**\n\n**How it works:** Measures the average change in prices for a basket of goods and services, but EXCLUDES owner-occupiers' housing costs (like mortgage interest).\n\n**Who it is for:** Renters and for international comparisons (as it follows standard global methodologies)."
)
show_rpi = st.sidebar.checkbox(
    "Show RPI Trajectory", 
    value=True,
    help="**Retail Prices Index (RPI)**\n\n**How it works:** A long-standing measure that tracks prices including mortgage interest payments and house depreciation.\n\n**Who it is for:** Frequently used in wage bargaining (Unions), setting rail fares, and calculating interest on student loans."
)

st.sidebar.header("Performance Scenarios")
show_outstanding = st.sidebar.checkbox(
    "Show Outstanding", 
    value=True, 
    help="**Outstanding**\n\nTop tier rating. Typically awarded to employees who significantly exceed all objectives and demonstrate exceptional behavior. Often limited to the top 10-20% of staff."
)
show_very_strong = st.sidebar.checkbox(
    "Show Very Strong", 
    value=True, 
    help="**Very Strong** (formerly Above Average)\n\nHigh performance rating. Awarded to employees who exceed expectations in critical areas and consistently deliver high-quality work."
)
show_successful = st.sidebar.checkbox(
    "Show Successful", 
    value=True, 
    help="**Successful** (formerly Average)\n\nStandard rating. Indicates the employee meets all role requirements and objectives. The majority of employees typically fall into this category."
)

st.sidebar.header("Footnote Adjustments")
apply_2022_adj = st.sidebar.checkbox("2022: Low/Median Earner Adjustment", value=True, help="Adds +1% for median salaries (30-50k) and +2% for low salaries (<=30k).")
apply_2023_adj = st.sidebar.checkbox("2023: Cost of Living Adjustment", value=True, help="Adds a flat +2% Cost of Living adjustment to all grades.")
apply_2024_adj = st.sidebar.checkbox("2024: Variance Adjustment", value=True, help="Adjusts based on salary band: Low salaries (<37k) +1%, High salaries (>50k) -1%.")

# --- DATA ---
years = [2020, 2021, 2022, 2023, 2024, 2025]

# Inflation Data (Percentage Change Year-on-Year - Year to March)
# 2020 is base (0% change for calculation context, inflation applies to subsequent years)
# Updated CPIH values based on ONS March figures: 
# 2021 (1.0), 2022 (6.2), 2023 (8.9), 2024 (3.8), 2025 (3.4)
inflation_data = {
    'CPIH': {2021: 1.0, 2022: 6.2, 2023: 8.9, 2024: 3.8, 2025: 3.4},
    'CPI':  {2021: 0.7, 2022: 7.0, 2023: 10.1, 2024: 3.2, 2025: 2.6},
    'RPI':  {2021: 1.5, 2022: 9.0, 2023: 13.5, 2024: 4.3, 2025: 3.2}
}

# Pay Awards (Outstanding / Very Strong / Successful)
# Format: {Year: [Outstanding, Very Strong, Successful]}
pay_rates = {
    2021: [3.25, 2.75, 2.30],
    2022: [3.25, 2.75, 2.30], 
    2023: [3.70, 2.70, 2.30], 
    2024: [3.70, 2.70, 2.30],
    2025: [3.70, 2.70, 2.30]
}

# --- 1. INFLATION OVERVIEW GRAPH ---
st.header("1. Annual Inflation Rates (Year to March)")
st.caption("This graph shows the raw inflation percentage for each year.")

# Create DataFrame for bar chart
inf_df = pd.DataFrame(inflation_data)
# Filter out 2020 as it's the base year with no inflation data in this context
plot_years = [y for y in years if y != 2020]

fig_inf = go.Figure()
fig_inf.add_trace(go.Bar(x=plot_years, y=[inflation_data['CPIH'][y] for y in plot_years], name='CPIH', marker_color='#c0392b'))
fig_inf.add_trace(go.Bar(x=plot_years, y=[inflation_data['CPI'][y] for y in plot_years], name='CPI', marker_color='#2980b9'))
fig_inf.add_trace(go.Bar(x=plot_years, y=[inflation_data['RPI'][y] for y in plot_years], name='RPI', marker_color='#8e44ad'))

fig_inf.update_layout(
    barmode='group',
    xaxis_title="Year",
    yaxis_title="Inflation Rate (%)",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
)
st.plotly_chart(fig_inf, use_container_width=True)


# --- CALCULATION LOGIC ---
def calculate_trajectory(mode):
    # Initialize
    trajectory = [start_salary]
    current_val = start_salary
    meta_changes = [0.0] 

    for i in range(1, len(years)):
        year = years[i]
        pct_change = 0.0
        
        # Salary Logic
        if mode in ['successful', 'verystrong', 'outstanding']:
            # Determine Base Rate (Indices: 0=Outstanding, 1=Very Strong, 2=Successful)
            if mode == 'outstanding': idx = 0 
            elif mode == 'verystrong': idx = 1 
            else: idx = 2 # successful
            
            base = pay_rates[year][idx]
            
            # Apply Adjustments
            adj = 0.0
            
            # 2022: Low Earner Adjustment
            # Logic: 30-50k = +1%, <=30k = +2%
            if year == 2022 and apply_2022_adj:
                if current_val <= 30000:
                    adj = 2.0
                elif current_val <= 50000:
                    adj = 1.0
            
            # 2023: Cost of Living Adjustment
            # Logic: Flat +2% to base option
            if year == 2023 and apply_2023_adj:
                adj = 2.0
                
            # 2024: Variance Adjustment
            # Logic: Low (<37k) +1%, High (>50k) -1%
            if year == 2024 and apply_2024_adj:
                if current_val < 37000:
                    adj = 1.0
                elif current_val > 50000:
                    adj = -1.0
            
            pct_change = base + adj
            
        # Inflation Logic (Compounding)
        elif mode == 'cpih': pct_change = inflation_data['CPIH'][year]
        elif mode == 'cpi': pct_change = inflation_data['CPI'][year]
        elif mode == 'rpi': pct_change = inflation_data['RPI'][year]
            
        current_val = current_val * (1 + pct_change / 100)
        trajectory.append(current_val)
        meta_changes.append(pct_change)
        
    return trajectory, meta_changes

# Calculate Trajectories
sal_successful, m_successful = calculate_trajectory('successful')
sal_verystrong, m_verystrong = calculate_trajectory('verystrong')
sal_outstanding, m_outstanding = calculate_trajectory('outstanding')

inf_cpih, m_cpih = calculate_trajectory('cpih')
inf_cpi, m_cpi = calculate_trajectory('cpi')
inf_rpi, m_rpi = calculate_trajectory('rpi')

# --- 2. SALARY VS INFLATION GRAPH ---
st.header("2. Salary Trajectory vs Inflation")
st.caption(f"Projected value of a £{start_salary:,} starting salary if pegged to inflation vs. actual pay awards.")

fig = go.Figure()

# Inflation Lines
if show_rpi:
    fig.add_trace(go.Scatter(
        x=years, y=inf_rpi, name='RPI Track', mode='lines+markers',
        line=dict(color='#8e44ad', width=2, dash='dot'),
        hovertemplate="£%{y:,.0f} (+%{customdata}%)", customdata=m_rpi
    ))
if show_cpi:
    fig.add_trace(go.Scatter(
        x=years, y=inf_cpi, name='CPI Track', mode='lines+markers',
        line=dict(color='#2980b9', width=2, dash='dash'),
        hovertemplate="£%{y:,.0f} (+%{customdata}%)", customdata=m_cpi
    ))
if show_cpih:
    fig.add_trace(go.Scatter(
        x=years, y=inf_cpih, name='CPIH Track', mode='lines+markers',
        line=dict(color='#c0392b', width=2, dash='dash'),
        hovertemplate="£%{y:,.0f} (+%{customdata}%)", customdata=m_cpih
    ))

# Salary Lines
if show_outstanding:
    fig.add_trace(go.Scatter(
        x=years, y=sal_outstanding, name='Outstanding Performance', mode='lines+markers',
        line=dict(color='#27ae60', width=3),
        hovertemplate="£%{y:,.0f} (+%{customdata:.2f}%)", customdata=m_outstanding
    ))

if show_very_strong:
    fig.add_trace(go.Scatter(
        x=years, y=sal_verystrong, name='Very Strong Performance', mode='lines+markers',
        line=dict(color='#3498db', width=3),
        hovertemplate="£%{y:,.0f} (+%{customdata:.2f}%)", customdata=m_verystrong
    ))

if show_successful:
    fig.add_trace(go.Scatter(
        x=years, y=sal_successful, name='Successful Performance', mode='lines+markers',
        line=dict(color='#f39c12', width=3),
        hovertemplate="£%{y:,.0f} (+%{customdata:.2f}%)", customdata=m_successful
    ))

fig.update_layout(
    xaxis_title="Year", yaxis_title="Salary (£)",
    hovermode="x unified", template="plotly_white",
    legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
)
st.plotly_chart(fig, use_container_width=True)

# --- 3. PAY EROSION GRAPH ---
st.header("3. Real Wage Erosion (Purchasing Power)")
st.caption("This graph illustrates the cumulative % change in 'Real Terms' salary relative to 2020. A negative value indicates you are effectively poorer than in 2020.")

def calculate_real_term_change(nominal_trajectory, inflation_trajectory):
    real_change = []
    for i in range(len(years)):
        # Real Value = Nominal Salary / (Inflation Index / Base Index)
        # Inflation Index ratio is simply inflation_trajectory[i] / start_salary
        real_value = nominal_trajectory[i] / (inflation_trajectory[i] / start_salary)
        pct_diff = ((real_value - start_salary) / start_salary) * 100
        real_change.append(pct_diff)
    return real_change

# Allow user to toggle comparison index for erosion
erosion_index = st.radio("Select Inflation Index for Erosion Calculation:", ["CPIH", "CPI", "RPI"], horizontal=True)

if erosion_index == "CPIH": ref_traj = inf_cpih
elif erosion_index == "CPI": ref_traj = inf_cpi
else: ref_traj = inf_rpi

# Recalculate based on selection
real_successful = calculate_real_term_change(sal_successful, ref_traj)
real_verystrong = calculate_real_term_change(sal_verystrong, ref_traj)
real_outstanding = calculate_real_term_change(sal_outstanding, ref_traj)

fig_erosion = go.Figure()

# Add zero line
fig_erosion.add_hline(y=0, line_dash="dot", line_color="black", annotation_text="2020 Purchasing Power")

if show_outstanding:
    fig_erosion.add_trace(go.Scatter(
        x=years, y=real_outstanding, name='Outstanding (Real Terms)',
        mode='lines+markers', line=dict(color='#27ae60', width=3),
        hovertemplate="%{y:.1f}%"
    ))

if show_very_strong:
    fig_erosion.add_trace(go.Scatter(
        x=years, y=real_verystrong, name='Very Strong (Real Terms)',
        mode='lines+markers', line=dict(color='#3498db', width=3),
        hovertemplate="%{y:.1f}%"
    ))

if show_successful:
    fig_erosion.add_trace(go.Scatter(
        x=years, y=real_successful, name='Successful (Real Terms)',
        mode='lines+markers', line=dict(color='#f39c12', width=3),
        hovertemplate="%{y:.1f}%"
    ))

# Fill area below zero to show "Erosion Zone"
# We need to determine the min Y to set the rectangle bottom
min_vals = [0]
if show_successful: min_vals.append(min(real_successful))
if show_very_strong: min_vals.append(min(real_verystrong))
if show_outstanding: min_vals.append(min(real_outstanding))

max_vals = [0]
if show_successful: max_vals.append(max(real_successful))
if show_very_strong: max_vals.append(max(real_verystrong))
if show_outstanding: max_vals.append(max(real_outstanding))

min_y = min(min_vals)
max_y = max(max_vals)

fig_erosion.add_hrect(y0=-100, y1=0, fillcolor="red", opacity=0.1, layer="below", line_width=0)

fig_erosion.update_layout(
    xaxis_title="Year", 
    yaxis_title=f"Cumulative Change vs {erosion_index} (%)",
    yaxis_range=[min_y - 5, max_y + 5],
    hovermode="x unified", 
    template="plotly_white",
    legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
)
st.plotly_chart(fig_erosion, use_container_width=True)

# --- METRICS ---
st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric("2025 CPIH Cumulative", f"£{int(inf_cpih[-1]):,}", delta=f"{(inf_cpih[-1]/start_salary - 1)*100:.1f}% vs 2020", delta_color="inverse")
col2.metric("2025 Successful Salary", f"£{int(sal_successful[-1]):,}", delta=f"{(sal_successful[-1]/start_salary - 1)*100:.1f}% vs 2020")
real_loss_val = real_successful[-1]
col3.metric(f"Real Terms Impact ({erosion_index})", f"{real_loss_val:.1f}%", delta_color="normal" if real_loss_val > 0 else "inverse")
