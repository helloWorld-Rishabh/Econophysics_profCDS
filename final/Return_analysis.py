import pandas as pd
import numpy as np

def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """
    Loads the 'monthly_pe_ratio.csv' file.
    """
    try:
        # Load the CSV file, parsing 'Date' as the index
        df = pd.read_csv(
            filepath,
            parse_dates=['Date'],
            index_col='Date'
        )
        
        if df.empty:
            raise ValueError("The file is empty.")
            
        print(f"Successfully loaded '{filepath}'.")
        print(f"Data ranges from {df.index.min().date()} to {df.index.max().date()}.\n")
        
        return df

    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        print("Please run 'calculate_pe_ratio.py' first to generate this file.")
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred during data loading: {e}")
        return pd.DataFrame()

def calculate_pe_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates returns for P/E ratio.
    
    - 1-Month P/E % Change
    - 1-Year (12-Month) Rolling P/E % Change
    """
    
    # 1. 1-Month P/E % Change (our base period)
    df['pe_change_1m'] = df['P/E_TTM'].pct_change() * 100
    
    # 2. 1-Year (12-Month) Rolling P/E % Change
    df['pe_change_1y'] = df['P/E_TTM'].pct_change(periods=12) * 100
        
    return df

def analyze_distribution(series: pd.Series, horizon_name: str):
    """
    Calculates and prints the key distribution metrics from the paper:
    PRP, RRR, and Modal Return.
    """
    print(f"--- {horizon_name} Return Analysis ---")
    
    data = series.dropna()
    
    if data.empty:
        print("No data to analyze.\n")
        return

    # 1. Probability of Positive Return (PRP)
    prp = (data > 0).mean() * 100
    
    # 2. Reward-Risk Ratio (RRR)
    positive_returns = data[data > 0]
    negative_returns = data[data < 0]
    
    avg_gain = positive_returns.mean()
    avg_loss = negative_returns.abs().mean()
    
    if pd.isna(avg_loss) or avg_loss == 0:
        rrr = float('inf')  # All returns were positive
    else:
        rrr = avg_gain / avg_loss
        
    # 3. Modal Return (Most Probable Return)
    # We find the center of the most frequent bin in a histogram
    # This approximates the 'mode' for continuous data
    counts, bins = np.histogram(data, bins=100)
    modal_bin_index = np.argmax(counts)
    modal_return = (bins[modal_bin_index] + bins[modal_bin_index + 1]) / 2

    # --- Print Results ---
    print(f"Total Periods:    {len(data)}")
    print(f"Modal Value:      {modal_return:.2f}")  # Renamed from Modal Return
    print(f"Probability > 0 (PRP): {prp:.2f}%")
    print(f"Avg. Gain:        {avg_gain:.2f}")  # Renamed from Avg. Gain
    print(f"Avg. Loss:        {avg_loss:.2f}")  # Renamed from Avg. Loss
    print(f"Reward-Risk (RRR): {rrr:.2f}")
    print("")

def main():
    FILE_PATH = 'monthly_pe_ratio_reliance.csv'
    
    df = load_and_clean_data(FILE_PATH)
    
    if df.empty:
        print("Exiting script due to data loading failure.")
        return
        
    df = calculate_pe_changes(df)
    
    # Run the analyses
    # 1. Analyze the distribution of the P/E ratio itself
    analyze_distribution(df['P/E_TTM'], "P/E (TTM) Ratio Distribution")
    
    # 2. Analyze the 1-Month change (return) of the P/E ratio
    analyze_distribution(df['pe_change_1m'], "1-Month P/E Change")
    
    # 3. Analyze the 1-Year change (return) of the P/E ratio
    analyze_distribution(df['pe_change_1y'], "1-Year (12-Month) P/E Change")


if __name__ == "__main__":
    main()