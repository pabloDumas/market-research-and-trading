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

## Author
**Pablo**  
*Last updated: 2025-10-23*
