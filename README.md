# market-research-and-trading
Aggregates data from AlphaVantage, Morningstar, and MarketSurge into one matrix, applies AutoGluon and ensemble models to predict optimal trades, and executes them via Interactive Brokers with daily real-time updates to maximize profit. — Pablo, 2025-10-23

# AutoGL Trade Orchestrator

## Overview
This project automates the full pipeline of data-driven trading:
1. **Data Aggregation** – Pulls market data from AlphaVantage, Morningstar, and MarketSurge.
2. **Data Consolidation** – Merges all data into a structured master matrix for analysis.
3. **Modeling** – Uses AutoGluon and ensemble models to learn from cross-source signals.
4. **Prediction & Trading** – Identifies optimal trades and executes them automatically via Interactive Brokers.
5. **Automation** – Daily scheduled runs for data refresh, retraining, and portfolio updates.

## Goals
- Build a self-improving trading system using diverse financial datasets.
- Leverage ensemble learning for robust signal detection.
- Maintain continuous synchronization with real-time market data.

### Top Predictors of Market Recessions  
1. **Yield Curve Inversion** – 10Y–2Y or 10Y–3M spread turning negative *(leads ~12–18 mo)*  Source: FRED (full free)
2. **Leading Economic Index (LEI)** – Sustained multi-month decline *(leads ~6–12 mo)*  Source: FRED (para free)
3. **ISM Manufacturing PMI** – Below 45 signals contraction *(leads ~6 mo)*  Source: Nasdaq Data Link (paid; not yet found)
4. **Consumer Confidence** – Sharp drop in expectations index *(leads ~6–9 mo)*  Source: FRED (para free)
5. **Jobless Claims** – Rising 4-week moving average *(leads ~3–6 mo)*    Source: FRED (free)
6. **Corporate Profits** – Sequential quarterly declines *(leads ~6–9 mo)*    Source: FRED (free)
7. **Credit Spreads** – Widening BBB-to-Treasury differential *(leads ~6–12 mo)*      Source: FRED (free)
8. **Housing Starts** – Sustained downturn *(leads ~8–12 mo)*      Source: FRED (free)  
9. **Retail Sales Growth** – Negative real YoY change *(leads ~3–6 mo)*       Source: FRED (free)  
10. **Industrial Production / Business Investment** – Slowing or contracting output *(leads ~3–6 mo)*  
11. **M2 Money Supply Growth** – Sudden contraction *(leads ~9–15 mo)*  
12. **Earnings Revisions** – Net downgrades > upgrades *(leads ~4–6 mo)*  
13. **Equity Market Breadth** – Fewer stocks making new highs *(leads ~6–9 mo)*  
14. **Volatility Index (VIX)** – Elevated for extended period *(coincident to 3 mo lead)*  
15. **Oil Price Spikes** – > 40 % rise in < 6 mo *(leads ~6–9 mo)*  
16. **Corporate Layoffs** – Rapid acceleration *(coincident to 3 mo lead)*  
17. **Business Inventories** – Rising faster than sales *(leads ~3–6 mo)*  
18. **Credit Card Delinquencies** – Upturn in defaults *(leads ~6–9 mo)*  
19. **Auto Sales** – Multi-month decline *(leads ~6 mo)*  
20. **Global PMI Composite** – Simultaneous regional contraction *(leads ~6–9 mo)*  
21. **Household Debt Burden / Financial Obligations** – Rising ratios signal stress *(leads ~6–9 mo)*  
22. **Unemployment (3-month avg unemployment rate rises ≥0.5 pp above its 12-month low) / Labor Market Slack** – Deterioration after tight cycle *(coincident to 3 mo lead)*
23. **CAPE / Shiller P/E** – Elevated cyclically adjusted P/E ratios precede below-average long-term returns *(leads ~24–60 mo for market downturns; best as 2–5 yr valuation risk indicator rather than short-term signal)*
24. **Buffet Indicator / Overall Market Evaluation** – Ratio of total U.S. stock-market capitalization to nominal GDP; gauges broad market valuation; historically fair = 80–100 %, over 150 % = expensive, over 200 % = bubble; recent ≈ 165 % (2025 Q4 vs peak 230 % in 2021 Q4); high values often precede below-trend returns (~24–48 mo lead).
25. **Market Concentration in Giants + Large Institutional Volume Drop** – Share of market cap in top 5–10 mega-caps (AAPL, MSFT, GOOGL, AMZN, NVDA etc.) combined with falling institutional volume; signals narrow breadth and fragility; recent: top 7 ≈ 33–35 % of S&P 500 (2024–2025) with ~20 % decline in institutional trading since 2021; often leads volatility spikes or corrections (~6–12 mo lead).

### Influential Economists & Models  
- **Campbell R. Harvey — Duke University**  
  - *Format:* Academic papers, media interviews, podcasts/YouTube  
  - *Metric:* Yield-curve inversion (term spread) as recession predictor — “8-for-8 since the 1960s.”  
  - *Data Source (Android):* FRED (Federal Reserve Economic Data app)  

- **Arturo Estrella — Former NY Fed Economist (with Mishkin et al.)**  
  - *Format:* NY Fed research notes and dashboards  
  - *Metric:* NY Fed recession probability model (10y–3m Treasury spread)  
  - *Data Source (Android):* Federal Reserve Bank of New York (Yield Curve Model PDF / FRED)  

- **Claudia Sahm — “ Sahm Rule ” Creator**  
  - *Format:* FRED series, policy briefs, podcasts  
  - *Metric:* Recession flag when 3-month avg unemployment rate ≥ 0.5 pp above 12-month low  
  - *Data Source (Android):* FRED mobile app (search “SAHMREALTIME”)  

- **Michael Kantrowitz — Piper Sandler**  
  - *Format:* Slides, interviews, podcasts  
  - *Metric:* H.O.P.E. framework (Housing → Orders → Profits → Employment)  
  - *Data Source (Android):* Investing.com or Trading Economics apps for macro data feeds  

- **Robert J. Shiller — Yale Economist / Nobel Laureate**  
  - *Format:* Books (*Irrational Exuberance*), papers, media  
  - *Metric:* CAPE (Shiller P/E) for long-term valuation and recession risk  
  - *Data Source (Android):* Shiller CAPE on FRED / Yahoo Finance API  

- **Lakshman Achuthan / ECRI (Economic Cycle Research Institute)**  
  - *Format:* Newsletters, TV segments, leading index updates  
  - *Metric:* Proprietary weekly leading index (WLI) composites  
  - *Data Source (Android):* ECRI mobile site / Business Insider coverage  

- **David Rosenberg — Rosenberg Research**  
  - *Format:* Macro research notes, interviews  
  - *Metric:* Focus on credit, profit, and cycle inflection signals  
  - *Data Source (Android):* Rosenberg Research website / Bloomberg app  

### Core Institutional Sources (Android-Accessible APIs / Apps)  
- **FRED (Federal Reserve Economic Data)** – comprehensive macro database (Android app + API)  
- **Trading Economics** – global economic indicators and forecasts (Android app + API)  
- **Investing.com** – market & macro data (Android app)  
- **Alpha Vantage** – financial and macro API (Android via custom Python scripts)  
- **Conference Board LEI** – monthly press releases (Android browser accessible)  


## Author
**Pablo**  
*Last updated: 2025-10-23*
