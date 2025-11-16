import pandas as pd
import numpy as np
from scipy.stats import entropy
import nolds

def load_data(filepath: str) -> pd.DataFrame:
    """
    Loads the 'monthly_pe_ratio_reliance.csv' file.
    """
    try:
        df = pd.read_csv(filepath, parse_dates=['Date'], index_col='Date')
        if df.empty:
            raise ValueError("File is empty.")
        print(f"Successfully loaded '{filepath}'.\n")
        
        # Calculate 1-Month Price Returns (as % change)
        df['price_return_1m'] = df['Price'].pct_change() * 100
        
        return df
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

def calculate_shannon_entropy(series: pd.Series, num_bins: int = 50) -> float:
    """
    Calculates the Shannon Normalized Entropy (SNE).
    Measures the randomness/unpredictability of the series.
    
    Result: 0 (perfectly predictable) to 1 (purely random).
    """
    try:
        data = series.dropna().values
        # Create a histogram (probability distribution)
        counts, bin_edges = np.histogram(data, bins=num_bins)
        
        # Calculate entropy
        # We use the counts directly, scipy normalizes it
        H = entropy(counts, base=2)
        
        # Normalize the entropy
        max_entropy = np.log2(num_bins)
        SNE = H / max_entropy
        
        return SNE
    except Exception as e:
        print(f"  - Could not calculate SNE: {e}")
        return np.nan

def calculate_hurst_exponent(series: pd.Series) -> float:
    """
    Calculates the Hurst Exponent (HE).
    Measures "memory" or "persistence".
    
    Result:
    HE > 0.5: Persistent (trending) behavior
    HE = 0.5: Random Walk (no memory)
    HE < 0.5: Anti-persistent (mean-reverting) behavior
    """
    try:
        data = series.dropna().values
        # Using nolds implementation of Rescaled Range (RS) analysis
        H = nolds.hurst_rs(data)
        return H
    except Exception as e:
        print(f"  - Could not calculate Hurst: {e}")
        return np.nan

def calculate_lyapunov_exponent(series: pd.Series) -> float:
    """
    Calculates the Largest Lyapunov Exponent (LLE).
    Measures sensitivity to initial conditions (chaos).
    
    Result:
    LLE > 0: Chaotic (highly sensitive, unpredictable)
    LLE <= 0: Non-chaotic (predictable)
    """
    try:
        data = series.dropna().values
        # This calculates the LLE using Rosenstein's method
        # It's computationally intensive
        LLE = nolds.lyap_r(data)
        return LLE
    except Exception as e:
        # This often fails if the series is too short or not "embeddable"
        print(f"  - Could not calculate Lyapunov: {e}")
        return np.nan

def main():
    FILE_PATH = 'monthly_pe_ratio_HDFC.csv'
    
    df = load_data(FILE_PATH)
    if df.empty:
        return

    # --- Analysis 1: P/E (TTM) Ratio Dynamics ---
    print("--- Analyzing Complexity of: P/E (TTM) Ratio ---")
    pe_series = df['P/E_TTM']
    
    sne_pe = calculate_shannon_entropy(pe_series)
    he_pe = calculate_hurst_exponent(pe_series)
    lle_pe = calculate_lyapunov_exponent(pe_series)
    
    print(f"  Shannon Entropy (SNE): {sne_pe:.3f}")
    print(f"  Hurst Exponent (HE):   {he_pe:.3f}")
    print(f"  Lyapunov Exponent (LLE): {lle_pe:.3f}")
    print("\n")

    # --- Analysis 2: Price Return (1-Month) Dynamics ---
    print("--- Analyzing Complexity of: 1-Month Price Returns ---")
    return_series = df['price_return_1m']
    
    sne_return = calculate_shannon_entropy(return_series)
    he_return = calculate_hurst_exponent(return_series)
    lle_return = calculate_lyapunov_exponent(return_series)
    
    print(f"  Shannon Entropy (SNE): {sne_return:.3f}")
    print(f"  Hurst Exponent (HE):   {he_return:.3f}")
    print(f"  Lyapunov Exponent (LLE): {lle_return:.3f}")
    print("\n")

    # --- How to Interpret These Results ---
    print("="*50)
    print("HOW TO INTERPRET YOUR RELIANCE DATA:")
    print("="*50)
    
    if he_pe > 0.52:
        print(f"[P/E RATIO]: Your Hurst Exponent (HE) of {he_pe:.3f} is > 0.5.")
        print("  -> INTERPRETATION: This suggests the P/E ratio is 'persistent' or 'trending'.")
        print("     When the valuation gets high, it tends to *stay* high (and vice-versa).")
        print("     It does *not* immediately snap back to the average.")
    elif he_pe < 0.48:
        print(f"[P/E RATIO]: Your Hurst Exponent (HE) of {he_pe:.3f} is < 0.5.")
        print("  -> INTERPRETATION: This suggests the P/E ratio is 'anti-persistent' or 'mean-reverting'.")
        print("     A high valuation is quickly followed by a move lower (and vice-versa).")
    else:
        print(f"[P/E RATIO]: Your Hurst Exponent (HE) of {he_pe:.3f} is near 0.5.")
        print("  -> INTERPRETATION: This suggests the P/E ratio moves like a 'random walk' with no memory.")

    if lle_pe > 0:
        print(f"\n[P/E RATIO]: Your Lyapunov Exponent (LLE) of {lle_pe:.3f} is POSITIVE.")
        print("  -> INTERPRETATION: This is strong evidence that the Reliance valuation is a 'chaotic' system.")
        print("     It is highly sensitive to small changes and its short-term direction is fundamentally unpredictable.")
    else:
        print(f"\n[P/E RATIO]: Your Lyapunov Exponent (LLE) of {lle_pe:.3f} is NOT positive.")
        print("  -> INTERPRETATION: The Reliance valuation does *not* show signs of mathematical chaos.")
        
    print("\n---\n")

    if he_return < 0.48:
        print(f"[PRICE RETURNS]: Your Hurst Exponent (HE) of {he_return:.3f} is < 0.5.")
        print("  -> INTERPRETATION: Monthly returns are 'anti-persistent' (mean-reverting).")
        print("     A positive month is slightly more likely to be followed by a negative month.")
    elif he_return > 0.52:
         print(f"[PRICE RETURNS]: Your Hurst Exponent (HE) of {he_return:.3f} is > 0.5.")
         print("  -> INTERPRETATION: Monthly returns are 'persistent' (trending/momentum).")
         print("     A positive month is slightly more likely to be followed by another positive month.")
    else:
        print(f"[PRICE RETURNS]: Your Hurst Exponent (HE) of {he_return:.3f} is near 0.5.")
        print("  -> INTERPRETATION: This matches the 'Random Walk Hypothesis'.")
        print("     Past returns have no memory and no predictive power for future returns.")

if __name__ == "__main__":
    main()