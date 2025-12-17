import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Salary Truth Checker", layout="centered")

st.title("📉 The Real-Terms Salary Calculator")
st.write("Visualizing the gap between your pay rise and ONS inflation.")

# --- INPUTS ---
col1, col2 = st.columns(2)
start_salary = col1.number_input("Starting Salary (2017)", value=40000, step=1000)
optimistic_2023 = col2.checkbox("Assume 2023 'Plus' was additive?", value=True, help="If checked, 2023 raise = 2.3% + 2.5%. If unchecked, it's just 2.3%.")

# --- DATA ---
years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
inflation = [0.0, 2.6, 2.3, 1.7, 1.0, 2.5, 8.8, 4.2, 3.9] # 2017 is 0 relative to start

# Avg Worker (Successful / 3)
avg_raises = [0, 2.25, 2.25, 2.15, 2.3, 3.3, 4.8 if optimistic_2023 else 2.3, 2.3, 2.3]

# Above Avg Worker (Avg early, Strong later)
# 2022: 2.75+1, 2023: 2.7+2.5(opt), 2024: 2.7
strong_raises = [0, 2.25, 2.25, 2.15, 2.75, 3.75, 5.2 if optimistic_2023 else 2.7, 2.7, 2.7]

# --- CALCULATE ---
curr_avg = start_salary
curr_strong = start_salary
curr_inf = start_salary

data = []
for i in range(len(years)):
    # Apply raise (Raise in year X applies to Year X salary usually, but table implies Year X raise is based on past performance)
    # Model: You start 2017 at flat salary. 
    if i > 0:
        curr_avg *= (1 + avg_raises[i]/100)
        curr_strong *= (1 + strong_raises[i]/100)
        curr_inf *= (1 + inflation[i]/100)
    
    data.append({
        "Year": years[i],
        "Real Inflation Need": curr_inf,
        "Above Avg Salary": curr_strong,
        "Avg Salary": curr_avg
    })

df = pd.DataFrame(data)

# --- PLOT ---
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['Year'], df['Real Inflation Need'], label='Required to Stand Still (Inflation)', color='#e74c3c', linewidth=3, linestyle='--')
ax.plot(df['Year'], df['Above Avg Salary'], label='Above Avg Worker', color='#2ecc71', linewidth=3)
ax.plot(df['Year'], df['Avg Salary'], label='Avg Worker', color='#f1c40f', linewidth=3)

# Labels
final_inf = df['Real Inflation Need'].iloc[-1]
final_strong = df['Above Avg Salary'].iloc[-1]

ax.text(2025.1, final_inf, f"£{int(final_inf):,}", color='#e74c3c', fontweight='bold', va='center')
ax.text(2025.1, final_strong, f"£{int(final_strong):,}", color='#2ecc71', fontweight='bold', va='center')

ax.set_title(f"Salary vs Inflation (Start: £{start_salary:,})")
ax.grid(True, alpha=0.3)
ax.legend()

st.pyplot(fig)

# --- METRICS ---
loss = final_strong - final_inf
st.error(f"⚠️ Real Terms Loss (2025): £{int(loss):,}")
st.caption(f"You need to earn £{int(final_inf):,} today to match the purchasing power of your starting salary.")
