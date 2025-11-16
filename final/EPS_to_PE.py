import pandas as pd

def load_data(filepath: str) -> (pd.DataFrame, pd.DataFrame):
    """
    Loads both price and EPS data from the same CSV file.
    """
    try:
        # 1. Load Quarterly EPS Data (Columns A and B)
        eps_df = pd.read_csv(
            filepath,
            usecols=[0, 1],       # Columns A and B
            skiprows=1,           # Skip header
            names=['Date', 'EPS']
        )
        
        # 2. Load Monthly Price Data (Columns H and I)
        prices_df = pd.read_csv(
            filepath,
            usecols=[7, 8],       # Columns H and I
            skiprows=1,           # Skip header
            names=['Date', 'Price']
        )
        
        print("Successfully loaded raw price and EPS data.")
        return prices_df, eps_df

    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        print(f"An error occurred during data loading: {e}")
        return pd.DataFrame(), pd.DataFrame()

def clean_and_process_data(prices_df: pd.DataFrame, eps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and aligns the monthly price and quarterly EPS data
    to calculate a monthly P/E ratio based on TTM EPS.
    """
    
    # --- 1. Clean EPS Data ---
    # Use .copy() to avoid SettingWithCopyWarning
    eps_df = eps_df.dropna().copy()
    eps_df['Date'] = pd.to_datetime(eps_df['Date'], format='%d-%m-%Y', errors='coerce')
    # Use raw string (r'...') to avoid SyntaxWarning
    eps_df['EPS'] = eps_df['EPS'].replace(r'[\$]', '', regex=True).astype(float)
    eps_df = eps_df.dropna()
    
    # --- FIX: Handle duplicate dates ---
    # Sort by Date first to ensure we keep the latest entry if duplicates exist
    eps_df = eps_df.sort_values(by='Date')
    # Drop duplicate dates, keeping the last one
    eps_df = eps_df.drop_duplicates(subset=['Date'], keep='last')
    
    # Now it's safe to set the index
    eps_df = eps_df.set_index('Date')
    
    # --- 2. Clean Price Data ---
    # Use .copy() to avoid SettingWithCopyWarning
    prices_df = prices_df.dropna().copy()
    prices_df['Date'] = pd.to_datetime(prices_df['Date'], format='%d-%m-%Y', errors='coerce')
    # Use raw string (r'...') for regex
    prices_df['Price'] = prices_df['Price'].replace(r'[",]', '', regex=True).astype(float)
    prices_df = prices_df.dropna()
    
    # --- FIX: Handle duplicate dates ---
    # Sort by Date first to ensure we keep the latest entry if duplicates exist
    prices_df = prices_df.sort_values(by='Date')
    # Drop duplicate dates, keeping the last one
    prices_df = prices_df.drop_duplicates(subset=['Date'], keep='last')
    
    # Now it's safe to set the index
    prices_df = prices_df.set_index('Date')

    # --- 3. Process Data for Monthly P/E ---
    
    # Calculate Trailing Twelve Months (TTM) EPS from the quarterly data
    # This is the sum of the last 4 quarters of earnings.
    quarterly_ttm_eps = eps_df['EPS'].rolling(window=4).sum().dropna()
    
    # --- 4. Merge Data [FIXED LOGIC] ---
    
    # We have monthly prices (e.g., '01-09-2025') and
    # quarterly TTM EPS (e.g., '30-09-2025').
    
    # We reindex the quarterly TTM EPS to the monthly price index.
    # method='ffill' (forward-fill) applies the last known
    # TTM EPS value to all subsequent months until a new one is reported.
    
    # Ensure both indexes are unique before reindexing
    if not prices_df.index.is_unique:
        print("Error: Price index is still not unique after cleaning.")
        return pd.DataFrame()
    if not quarterly_ttm_eps.index.is_unique:
        print("Error: TTM EPS index is not unique.")
        return pd.DataFrame()

    ttm_eps_monthly = quarterly_ttm_eps.reindex(prices_df.index, method='ffill')
    
    # Now, create the combined DataFrame from the price data
    combined_df = prices_df.copy()
    combined_df['TTM_EPS'] = ttm_eps_monthly
    
    # Drop any rows at the beginning that couldn't be filled
    # (i.e., before the first 4 quarters of EPS were available)
    combined_df = combined_df.dropna(subset=['Price', 'TTM_EPS'])
    
    # --- 5. Calculate P/E Ratio ---
    # P/E = Monthly Price / Last Reported TTM EPS
    combined_df['P/E_TTM'] = combined_df['Price'] / combined_df['TTM_EPS']
    
    # Clean up for final output
    final_df = combined_df[['Price', 'TTM_EPS', 'P/E_TTM']].dropna()
    
    return final_df

def main():
    FILE_PATH = 'HDFCRaw.csv'
    OUTPUT_PATH = 'monthly_pe_ratio_HDFC.csv'
    
    prices_df, eps_df = load_data(FILE_PATH)
    
    if prices_df.empty or eps_df.empty:
        print("Exiting script due to data loading failure.")
        return
        
    monthly_pe_df = clean_and_process_data(prices_df, eps_df)
    
    if monthly_pe_df.empty:
        print("No data remained after processing. Check file format or date alignment.")
    else:
        # Save the results to a new CSV
        monthly_pe_df.to_csv(OUTPUT_PATH)
        
        print(f"\nSuccessfully calculated monthly P/E (TTM).")
        print(f"Data saved to: {OUTPUT_PATH}")
        
        # Print the last 5 months as a preview
        print("\n--- Latest Monthly P/E Ratios (TTM) ---")
        print(monthly_pe_df.tail())

if __name__ == "__main__":
    main()