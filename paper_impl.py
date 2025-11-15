import pandas as pd
import numpy as np

# --- 1. Define File Names and Load Data ---
# Note: Assuming files are named 'NIFTY 50-01-01-2024-to-31-12-2024.csv' (Price) 
# and 'NIFTY 50-yield-01-01-2024-to-31-12-2024.csv' (P/E)
file_name_2024_price = "NIFTY 50-01-01-2024-to-31-12-2024.csv"
file_name_2024_pe = "NIFTY 50-yield-01-01-2024-to-31-12-2024.csv"

# Load Price Data and clean
df_price = pd.read_csv(file_name_2024_price)
df_price.columns = df_price.columns.str.strip()
df_price['Date'] = pd.to_datetime(df_price['Date'], errors='coerce', infer_datetime_format=True)
df_price = df_price[['Date', 'Close']].dropna()

# Load P/E Data and clean
df_pe = pd.read_csv(file_name_2024_pe)
df_pe.columns = df_pe.columns.str.strip()
df_pe = df_pe.rename(columns={'P/E': 'PE_Ratio'})
df_pe['Date'] = pd.to_datetime(df_pe['Date'], errors='coerce', infer_datetime_format=True)
df_pe = df_pe[['Date', 'PE_Ratio']].dropna()

# --- 2. Merge Data and Initial Calculations ---
df_merged = pd.merge(df_price, df_pe, on='Date', how='inner').sort_values(by='Date').reset_index(drop=True)

# Calculate Daily Return (R_t)
df_merged['Daily_Return'] = df_merged['Close'].pct_change() * 100

# Calculate EPS Proxy (EPS_t = P_t / (P/E)_t) - Section 4.2
df_merged['EPS_Proxy'] = df_merged['Close'] / df_merged['PE_Ratio']

# Drop the first row (NaN return)
df_merged = df_merged.dropna().reset_index(drop=True)

# --- 3. Define Valuation Regimes and Conditional Analysis ---

# Define Valuation Regimes (P/E bands, Section 4.2.1)
def map_pe_to_regime(pe):
    if pe < 13:
        return 'P/E < 13: No Risk Zone'
    elif 13 <= pe < 16:
        return 'P/E 13-16: Low Risk'
    elif 16 <= pe < 22:
        return 'P/E 16-22: Moderate Risk'
    elif 22 <= pe < 27:
        return 'P/E 22-27: High Risk'
    elif pe >= 27:
        return 'P/E > 27: Very High Risk'
    return 'Undefined'

df_merged['Valuation_Regime'] = df_merged['PE_Ratio'].apply(map_pe_to_regime)

# Define custom functions for PRP (Probability of Positive Return) and NRP (Negative Return Probability)
def calculate_prp(series):
    return (series > 0).mean()

def calculate_nrp(series):
    return (series < 0).mean()

# Conditional Return Analysis (Daily Horizon, Section 4.2)
conditional_analysis = df_merged.groupby('Valuation_Regime')['Daily_Return'].agg(
    Count='size',
    Min_Return='min',
    Max_Return='max',
    Mean_Return='mean',
    PRP=calculate_prp,
    NRP=calculate_nrp
).reset_index()

# Calculate Reward-Risk Ratio (RRR = PRP / NRP) - Section 4.2
conditional_analysis['RRR'] = np.where(
    conditional_analysis['NRP'] == 0,
    np.inf,
    conditional_analysis['PRP'] / conditional_analysis['NRP']
)

# Filter out regimes with no observations in 2024 and format
conditional_analysis = conditional_analysis[conditional_analysis['Count'] > 0]
conditional_analysis['Min_Return'] = conditional_analysis['Min_Return'].round(4)
conditional_analysis['Max_Return'] = conditional_analysis['Max_Return'].round(4)
conditional_analysis['Mean_Return'] = conditional_analysis['Mean_Return'].round(4)
conditional_analysis['PRP'] = conditional_analysis['PRP'].round(4)
conditional_analysis['NRP'] = conditional_analysis['NRP'].round(4)
conditional_analysis = conditional_analysis.sort_values(by='RRR', ascending=False)

# --- 4. Print and Save Output ---
print("\n--- Conditional Daily Return Analysis (Daily Horizon for 2024) ---")
print("This output shows risk/reward metrics conditioned on the P/E band at market entry.")
print(conditional_analysis.to_markdown(index=False))

print("\n--- EPS Proxy and Regime Sample (Head) ---")
print(df_merged[['Date', 'Close', 'PE_Ratio', 'EPS_Proxy', 'Daily_Return', 'Valuation_Regime']].head().to_markdown(index=False))

# Save the conditional analysis results
conditional_analysis.to_csv('nifty_50_conditional_analysis_2024.csv', index=False)