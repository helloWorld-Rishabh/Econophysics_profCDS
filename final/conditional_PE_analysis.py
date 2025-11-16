import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def load_data(filepath: str) -> pd.DataFrame:
    """
    Loads the 'monthly_pe_ratio_reliance.csv' file.
    """
    try:
        df = pd.read_csv(filepath, parse_dates=['Date'], index_col='Date')
        if df.empty:
            raise ValueError("File is empty.")
        print(f"Successfully loaded '{filepath}'.")
        print(f"Data ranges from {df.index.min().date()} to {df.index.max().date()}.\n")
        return df
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

def calculate_future_cagrs(df: pd.DataFrame, horizons_years: list) -> pd.DataFrame:
    """
    Calculates the Compound Annual Growth Rate (CAGR) for future periods.
    """
    df_out = df.copy()
    print("Calculating future CAGRs for all horizons...")
    for k in horizons_years:
        periods = 12 * k  # 12 months * k years
        col_name = f'cagr_fwd_{k}y'
        
        # Get the price 'periods' months into the future
        future_price = df_out['Price'].shift(-periods)
        
        # Calculate (Future Price / Current Price)
        price_ratio = future_price / df_out['Price']
        
        # Calculate CAGR: (Price Ratio) ^ (1 / k) - 1
        # We multiply by 100 at the end to get percentage
        df_out[col_name] = (np.power(price_ratio, 1/k) - 1) * 100
        
    return df_out

def plot_pe_distribution(df: pd.DataFrame):
    """
    Plots a histogram of the P/E ratio to identify valuation regimes.
    This is analogous to Figure 9 in the paper.
    """
    pe_data = df['P/E_TTM'].dropna()
    
    # Calculate statistics
    mean_pe = pe_data.mean()
    median_pe = pe_data.median()
    q1_pe = pe_data.quantile(0.25)
    q3_pe = pe_data.quantile(0.75)
    std_pe = pe_data.std()

    print("--- P/E (TTM) Ratio Distribution Stats ---")
    print(f"Mean P/E:   {mean_pe:.2f}")
    print(f"Median P/E: {median_pe:.2f}")
    print(f"Std Dev:    {std_pe:.2f}")
    print(f"25th Pctl (Q1): {q1_pe:.2f} (Considered 'Low')")
    print(f"75th Pctl (Q3): {q3_pe:.2f} (Considered 'High')")
    print("------------------------------------------\n")

    plt.figure(figsize=(12, 7))
    sns.histplot(pe_data, kde=True, bins=50, color='skyblue', fill=True)
    
    # Add vertical lines for key stats
    plt.axvline(mean_pe, color='red', linestyle='--', label=f'Mean: {mean_pe:.2f}')
    plt.axvline(median_pe, color='green', linestyle='-', label=f'Median: {median_pe:.2f}')
    plt.axvline(q1_pe, color='orange', linestyle=':', label=f'Q1 (25th): {q1_pe:.2f}')
    plt.axvline(q3_pe, color='purple', linestyle=':', label=f'Q3 (75th): {q3_pe:.2f}')
    
    plt.title('Reliance P/E (TTM) Ratio Distribution (Est. 2011-2025)', fontsize=16)
    plt.xlabel('P/E (TTM) Ratio', fontsize=12)
    plt.ylabel('Frequency (Count of Months)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)

def run_conditional_analysis(df: pd.DataFrame, horizons_years: list) -> pd.DataFrame:
    """
    Performs the core conditional analysis, replicating Table A.6 from the paper.
    It groups by P/E bands and calculates PRP, NRP, and RRR for each future horizon.
    """
    
    # Define P/E bands using quartiles (a robust, data-driven method)
    pe_data = df['P/E_TTM']
    q1 = pe_data.quantile(0.25)
    q2 = pe_data.quantile(0.50)
    q3 = pe_data.quantile(0.75)
    
    # Create labels for the P/E bands
    # (e.g., "Q1: < 22.1")
    band_labels = [
        f"Q1: Low P/E (< {q1:.1f})",
        f"Q2: Mid-Low P/E ({q1:.1f}-{q2:.1f})",
        f"Q3: Mid-High P/E ({q2:.1f}-{q3:.1f})",
        f"Q4: High P/E (> {q3:.1f})"
    ]
    
    df['pe_band'] = pd.qcut(df['P/E_TTM'], q=4, labels=band_labels)
    
    print("Running Conditional Analysis by P/E Band...")
    
    results = []
    
    # Group by the P/E bands we just created
    for band_name, group in df.groupby('pe_band'):
        for k in horizons_years:
            col_name = f'cagr_fwd_{k}y'
            series = group[col_name].dropna()
            
            if series.empty:
                continue
                
            # 1. Probability of Positive Return (PRP)
            prp = (series > 0).mean()
            
            # 2. Probability of Negative Return (NRP)
            nrp = (series < 0).mean()
            
            # 3. Reward-Risk Ratio (RRR)
            positive_returns = series[series > 0]
            negative_returns = series[series < 0]
            
            avg_gain = positive_returns.mean()
            avg_loss = negative_returns.abs().mean()
            
            if pd.isna(avg_loss) or avg_loss == 0:
                rrr = np.inf  # All returns were positive
            else:
                rrr = avg_gain / avg_loss
            
            results.append({
                'P/E Band': band_name,
                'Horizon (Years)': k,
                'PRP': prp,
                'NRP': nrp,
                'RRR': rrr
            })
            
    return pd.DataFrame(results)

def plot_analysis_heatmaps(results_df: pd.DataFrame):
    """
    Creates three heatmaps to visualize the conditional analysis results:
    1. PRP (Probability of Positive Return)
    2. NRP (Probability of Negative Return)
    3. RRR (Reward-Risk Ratio)
    """
    if results_df.empty:
        print("Cannot plot heatmaps: No results to analyze.")
        return

    # Pivot the data into a grid format suitable for heatmaps
    prp_pivot = results_df.pivot(index='P/E Band', columns='Horizon (Years)', values='PRP')
    nrp_pivot = results_df.pivot(index='P/E Band', columns='Horizon (Years)', values='NRP')
    rrr_pivot = results_df.pivot(index='P/E Band', columns='Horizon (Years)', values='RRR')

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 21))
    fig.suptitle('Conditional Analysis: Starting P/E vs. Future Returns', fontsize=20, y=1.02)

    # Plot 1: Probability of Positive Return (PRP)
    sns.heatmap(prp_pivot, annot=True, fmt=".1%", cmap="Greens", ax=ax1,
                linewidths=.5, cbar_kws={'label': 'Probability'})
    ax1.set_title('Probability of Positive Return (PRP)', fontsize=16)
    ax1.set_xlabel('Future Holding Period')
    ax1.set_ylabel('Starting P/E (TTM) Band')

    # Plot 2: Probability of Negative Return (NRP)
    sns.heatmap(nrp_pivot, annot=True, fmt=".1%", cmap="Reds", ax=ax2,
                linewidths=.5, cbar_kws={'label': 'Probability'})
    ax2.set_title('Probability of Negative Return (NRP) - "Risk"', fontsize=16)
    ax2.set_xlabel('Future Holding Period')
    ax2.set_ylabel('Starting P/E (TTM) Band')

    # Plot 3: Reward-Risk Ratio (RRR)
    # Handle potential 'inf' values for display
    rrr_pivot_display = rrr_pivot.replace(np.inf, 999) 
    sns.heatmap(rrr_pivot_display, annot=True, fmt=".2f", cmap="coolwarm", ax=ax3,
                linewidths=.5, center=1.0, cbar_kws={'label': 'Ratio (Avg Gain / Avg Loss)'})
    ax3.set_title('Reward-Risk Ratio (RRR)', fontsize=16)
    ax3.set_xlabel('Future Holding Period')
    ax3.set_ylabel('Starting P/E (TTM) Band')

    plt.tight_layout()

def plot_pe_vs_future_return_scatter(df: pd.DataFrame, horizon_years: int):
    """
    Creates a scatter plot of Starting P/E vs. Future CAGR for a specific horizon.
    This gives a more granular view than the binned heatmaps.
    """
    col_name = f'cagr_fwd_{horizon_years}y'
    plot_df = df[['P/E_TTM', col_name]].dropna()

    plt.figure(figsize=(12, 7))
    # Using regplot with 'lowess=True' to fit a non-linear trend line
    sns.regplot(data=plot_df, x='P/E_TTM', y=col_name,
                lowess=True, scatter_kws={'alpha': 0.3, 'color': 'blue'},
                line_kws={'color': 'red', 'linestyle': '--', 'linewidth': 2})
    
    plt.title(f'Starting P/E (TTM) vs. Future {horizon_years}-Year CAGR', fontsize=16)
    plt.xlabel('Starting P/E (TTM) Ratio', fontsize=12)
    plt.ylabel(f'Future {horizon_years}-Year CAGR (%)', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.axhline(0, color='black', linestyle='-') # Add a line at 0% return

def main():
    FILE_PATH = 'monthly_pe_ratio_HDFC.csv'
    HORIZONS_TO_ANALYZE = [1, 2, 3, 5, 7]  # Analyze 1, 2, 3, 5, and 7-year forward returns
    SCATTER_PLOT_HORIZON = 3  # We will create a detailed scatter plot for the 3-year horizon
    
    # 1. Load Data
    df = load_data(FILE_PATH)
    if df.empty:
        return

    # 2. Calculate Future Returns
    df_with_returns = calculate_future_cagrs(df, HORIZONS_TO_ANALYZE)
    
    # 3. Plot P/E Distribution
    plot_pe_distribution(df_with_returns)
    
    # 4. Run Conditional Analysis
    results_df = run_conditional_analysis(df_with_returns, HORIZONS_TO_ANALYZE)
    
    print("\n--- Conditional Analysis Results Table ---")
    # Set display options to show all rows and RRR as 2-decimal float
    pd.set_option('display.max_rows', None)
    pd.options.display.float_format = '{:,.2f}'.format
    print(results_df.to_string())
    print("------------------------------------------\n")

    # 5. Plot Heatmaps
    plot_analysis_heatmaps(results_df)
    
    # 6. Plot Detailed Scatter
    plot_pe_vs_future_return_scatter(df_with_returns, SCATTER_PLOT_HORIZON)
    
    # 7. Show all plots
    print("Displaying plots... Close the plot windows to exit.")
    plt.show()

if __name__ == "__main__":
    main()