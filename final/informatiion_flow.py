import pandas as pd
import numpy as np
from sklearn.metrics import normalized_mutual_info_score
# Corrected import: transfer_entropy is directly under the main 'pyinform' module
from pyinform import transfer_entropy 
from pyinform.error import InformError

def load_data(filepath: str) -> pd.DataFrame:
    """
    Loads the 'monthly_pe_ratio_reliance.csv' file.
    """
    try:
        df = pd.read_csv(filepath, parse_dates=['Date'], index_col='Date')
        if df.empty:
            raise ValueError("File is empty.")
        print(f"Successfully loaded '{filepath}'.")
        
        # Calculate 1-Month Price Returns (as % change)
        df['return_1m'] = df['Price'].pct_change()
        
        # CRITICAL: We need to align the P/E (t) with the Return (t+1)
        # We are testing if P/E *today* predicts the return *next month*
        df['return_fwd_1m'] = df['return_1m'].shift(-1)
        
        # Drop any NaNs created by a) pct_change b) shifting
        df = df.dropna()
        
        print(f"Data prepared for analysis from {df.index.min().date()} to {df.index.max().date()}.\n")
        return df
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

def discretize_series(series: pd.Series, bins: int = 10) -> np.ndarray:
    """
    Converts a continuous series (like P/E or returns) into
    discrete bins (e.g., 0, 1, 2...9).
    This is required for both NMI and TE calculations.
    
    We use 'qcut' to create bins with equal numbers of samples
    (e.g., 10 bins, each with 10% of the data).
    """
    try:
        binned_series = pd.qcut(series, q=bins, labels=False, duplicates='drop')
        return binned_series.values
    except ValueError as e:
        print(f"  - Warning: Could not discretize series. Maybe not enough unique values?")
        print(f"    {e}")
        return None

def analyze_nmi(df: pd.DataFrame, bins: int = 10):
    """
    Calculates the Normalized Mutual Information (NMI) between
    P/E at time (t) and Return at time (t+1).
    
    Measures: How strong is the *total* relationship (linear or not)?
    Scale: 0 (no relationship) to 1 (perfect relationship).
    """
    print("--- 1. Normalized Mutual Information (NMI) Analysis ---")
    
    # Discretize both series
    pe_binned = discretize_series(df['P/E_TTM'], bins=bins)
    return_binned = discretize_series(df['return_fwd_1m'], bins=bins)
    
    if pe_binned is None or return_binned is None:
        print("Could not calculate NMI due to binning error.")
        return

    # Calculate NMI
    nmi = normalized_mutual_info_score(pe_binned, return_binned)
    
    print(f"NMI Score (P/E -> 1-Month Fwd Return): {nmi:.4f}")
    
    # Interpretation
    if nmi > 0.1:
        print(f"  -> INTERPRETATION: NMI of {nmi:.4f} is HIGH for financial data.")
        print("     This indicates a strong nonlinear relationship exists between P/E and next month's return.")
    elif nmi > 0.02:
        print(f"  -> INTERPRETATION: NMI of {nmi:.4f} is MODERATE.")
        print("     This indicates a genuine, but noisy, nonlinear relationship.")
    else:
        print(f"  -> INTERPRETATION: NMI of {nmi:.4f} is LOW.")
        print("     There is very little shared information or predictive link.")
    print("")

def analyze_transfer_entropy(df: pd.DataFrame, bins: int = 5):
    """
    Calculates the Transfer Entropy (TE) in both directions.
    
    Measures: The *directional* flow of information (causality).
    "Does P/E's past help predict Return's future more than vice-versa?"
    """
    print("--- 2. Transfer Entropy (TE) Analysis ---")
    
    # Discretize series for TE. Using fewer bins (e.g., 5) is
    # often more stable for TE.
    pe_discrete = discretize_series(df['P/E_TTM'], bins=bins)
    return_discrete = discretize_series(df['return_1m'], bins=bins) # Note: TE handles its own lagging
    
    if pe_discrete is None or return_discrete is None:
        print("Could not calculate TE due to binning error.")
        return

    # We need to drop the first row for alignment after pct_change
    pe_discrete = pe_discrete[1:]
    return_discrete = return_discrete[1:]
    
    try:
        # k=1 means "use 1 month of history to predict"
        k = 1 
        
        # Test Flow 1: P/E (leader) -> Returns (follower)
        # "Does knowing the P/E *today* reduce uncertainty about the Return *tomorrow*?"
        te_pe_to_return = transfer_entropy(pe_discrete, return_discrete, k=k)
        
        # Test Flow 2: Returns (leader) -> P/E (follower)
        # "Does knowing the Return *today* reduce uncertainty about the P/E *tomorrow*?"
        te_return_to_pe = transfer_entropy(return_discrete, pe_discrete, k=k)

        print(f"TE (P/E -> Returns):   {te_pe_to_return:.6f} nats")
        print(f"TE (Returns -> P/E):   {te_return_to_pe:.6f} nats")
        print("")

        # --- Interpretation ---
        if te_pe_to_return > te_return_to_pe:
            diff_pct = ((te_pe_to_return - te_return_to_pe) / te_return_to_pe) * 100
            print(f"  -> RESULT: Information flows more strongly from P/E to Returns (by {diff_pct:.2f}%).")
            print("  -> INTERPRETATION: This is the 'smoking gun' from the paper.")
            print("     It suggests Reliance's P/E ratio acts as a *predictive leader* (the 'cause')")
            print("     and its future returns are the *follower* (the 'effect').")
            print("     This validates using P/E as a strategic, predictive tool.")
            
        elif te_return_to_pe > te_pe_to_return:
            diff_pct = ((te_return_to_pe - te_pe_to_return) / te_pe_to_return) * 100
            print(f"  -> RESULT: Information flows more strongly from Returns to P/E (by {diff_pct:.2f}%).")
            print("  -> INTERPRETATION: This implies that past returns are the primary driver of P/E changes.")
            print("     It suggests P/E is a *follower* (a 'lagging indicator') and is simply")
            print("     reacting to price momentum, rather than predicting it.")

        else:
            print("  -> RESULT: Information flow is roughly equal.")
            print("  -> INTERPRETATION: No clear leader/follower detected; they may be co-dependent.")

    except InformError as e:
        print(f"An error occurred during TE calculation: {e}")
        print("This can happen if the data is too short or not 'noisy' enough.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    FILE_PATH = 'monthly_pe_ratio_HDFC.csv'
    
    df = load_data(FILE_PATH)
    if df.empty:
        return

    # 1. Analyze NMI (Strength)
    # How strong is the *total* relationship?
    # We use 10 bins for a granular check.
    analyze_nmi(df, bins=10)
    
    # 2. Analyze TE (Direction)
    # Which way does the information flow?
    # We use 5 bins for a more stable, robust check.
    analyze_transfer_entropy(df, bins=5)

if __name__ == "__main__":
    main()