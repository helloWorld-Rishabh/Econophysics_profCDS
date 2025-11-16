# **Multi-Scale Financial Analysis of Indian Equities (Reliance & HDFC)**

This repository contains a Python-based framework for conducting advanced, non-linear financial analysis on individual stocks. The methodology is a direct application of the principles outlined in the research paper **"Multi-Scale Analysis of Nifty 50: Return Characteristics, Valuation Dynamics and Market Complexity (1990-2024)"** by Prof. Chandradew Sharma.

The project moves beyond traditional linear models (like simple correlation) to analyze:

1. **Valuation Dynamics:** How does the P/E ratio behave over time?  
2. **Market Complexity:** Is the stock's behavior simple (linear) or complex and chaotic (nonlinear)?  
3. **Information Flow:** Does P/E *predict* future returns? (A causality test).  
4. **Conditional Returns:** "If I invest at a *low* P/E, what is my historical risk vs. reward?"

The analysis has been performed on Reliance Industries and can be replicated for HDFC Bank using the provided scripts.

## **Summary of Findings: Reliance Industries (2011-2025)**

The analysis of the Reliance Industries dataset (2011-2025) yielded several significant insights:

1. **P/E is a Causal Leader:** The analysis of information flow is the "smoking gun." The Transfer Entropy from P/E to Returns (0.540 nats) is **157.35% stronger** than the flow from Returns to P/E (0.210 nats). This provides mathematical evidence that the P/E ratio acts as a **predictive leader (the 'cause')** for future price movements (the 'effect').  
2. **Valuation is Chaotic & Trending:** The P/E ratio's complexity signature is fascinating:  
   * **Hurst Exponent (HE): 0.947:** This is an extremely high value, indicating **strong persistence (trending behavior)**. When Reliance's valuation gets high, it tends to *stay* high and trend further, rather than "snapping back" to the average.  
   * **Lyapunov Exponent (LLE): 0.014:** A positive LLE confirms the valuation is a **"chaotic" system**, making its short-term moves fundamentally unpredictable.  
3. **Price Returns are Mean-Reverting:** In direct contrast to its *valuation*, the 1-month *price returns* are anti-persistent (**Hurst Exponent: 0.356**). This suggests that a positive month is slightly more likely to be followed by a negative month (mean-reversion) on a short-term basis.  
4. **The "Reliance Anomaly" (High P/E ≠ High Risk):** Unlike the broader market, where a high P/E often signals a "danger zone," the data for Reliance shows the opposite.  
   * The **"Mid-Low P/E"** band (Q2: 43.5-52.1) had the *highest* 1-year risk, with a 36% chance of loss (NRP).  
   * The **"High P/E"** band (Q4: \> 71.2) had a *lower* 1-year risk (19% NRP) and a *better* risk-reward profile (4.75 RRR).  
   * **Interpretation:** For Reliance, a high P/E has historically been a sign of strong, persistent growth *momentum*, not a signal of overvaluation risk.  
5. **The 3-Year "Safety Net":** The "trapping period" for Reliance is **3 years**. For *all* investors, regardless of their entry valuation, the probability of being at a loss (NRP) dropped to **0.00%** after a 3-year holding period (and 2 years for the highest P/E band).

## **Data Prerequisites**

This project requires a specific, non-standard CSV format for the raw data. Both the Reliance and HDFC data files follow this structure:

* **Quarterly EPS** data is located in columns A and B.  
* **Monthly Price** data is located in columns H and I.

This project will **not** work on a standard financial CSV. It is custom-built to parse this exact file layout.

## **How to Use This Repository**

This project is broken into a "processing" script and four "analysis" scripts.

### **1\. Dependencies**

You must have the required Python libraries installed.

pip install pandas numpy matplotlib seaborn scipy nolds pyinform

### **2\. Workflow for Analyzing a Company**

To analyze a new company (e.g., HDFC), you must follow this two-step process.

#### **Step 1: Data Processing (Create the P/E File)**

First, you must process the raw data file.

1. Open the EPS\_to\_PE.py (or calculate\_pe\_ratio.py) script.  
2. Change the FILE\_PATH variable to your raw data file (e.g., HDFC\_HistoricalQuotes.csv).  
3. Change the OUTPUT\_PATH variable to your desired output (e.g., hdfc\_pe\_ratio.csv).  
4. Run the script:

python EPS\_to\_PE.py

This will generate a clean hdfc\_pe\_ratio.csv file, which is now ready for analysis.

#### **Step 2: Run the Analysis Scripts**

Now, you can run any of the four analysis scripts on your newly created file.

For **each** of the scripts below, you must:

1. Open the script.  
2. Change the FILE\_PATH variable at the top to point to your new file (e.g., FILE\_PATH \= 'hdfc\_pe\_ratio.csv').  
3. Run the script.

\# For conditional P/E bands vs. Future Returns (PRP, NRP, RRR)  
python reliance\_conditional\_analysis.py

\# For complexity metrics (Hurst, Chaos, Entropy)  
python reliance\_complexity\_analysis.py

\# For the causality test (NMI, Transfer Entropy)  
python reliance\_information\_flow.py

\# For basic volatility and distribution stats  
python reliance\_return\_analysis.py

## **Script Descriptions**

* EPS\_to\_PE.py: **(Run this first)** Reads the complex, raw HistoricalQuotes.csv file. It merges the quarterly EPS (as TTM EPS) with the monthly price data and exports a clean monthly\_pe\_ratio.csv file.  
* reliance\_conditional\_analysis.py: **(Main Analysis)** Loads the clean P/E file, defines valuation bands (quartiles), and calculates the future probability of profit (PRP), loss (NRP), and the Reward-Risk Ratio (RRR) for 1, 2, 3, 5, and 7-year horizons. Generates plots.  
* reliance\_complexity\_analysis.py: Loads the clean P/E file and analyzes the "personality" of the P/E ratio and price returns, calculating the Hurst Exponent (memory), Lyapunov Exponent (chaos), and Shannon Entropy (randomness).  
* reliance\_information\_flow.py: Loads the clean P/E file and performs the "causality" analysis. It proves whether P/E is a predictive *leader* or a lagging *follower* by using Normalized Mutual Information (NMI) and Transfer Entropy (TE).  
* reliance\_return\_analysis.py: Loads the clean P/E file and calculates the basic distribution statistics (Modal Value, RRR, etc.) for the P/E ratio and its 1-month/1-year changes.

## **Data Sources**

* **Reliance Monthly Price Data:** investing.com  
* **Reliance Quarterly EPS:** macrotrends.net  
* **HDFC Data:** (Please add your source)

## **Acknowledgment**

This project is a direct application of the framework and methodology presented by **Prof. Chandradew Sharma (Department of Physics, BITS Pilani, Goa Campus)** in his research on the Nifty 50\.
