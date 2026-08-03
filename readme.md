# Volume Delta Calculator (CVD Module)

A tool for calculating volume delta on any timeframe based on Bulk Volume Classification or Candle-Based Tick-Rule
Suitable for plotting Cumulative Volume Delta (CVD) and analyzing order flow.

## Features
- Loads minute-by-minute candles via CCXT 
- BVC or tick rule
- Aggregation to any timeframe (`1h`, `4h`, `1d`, ...)
- Caching of minute-by-minute data (Pickle) to conserve API quotas
- OHLCV visualization + delta histogram

## How to use
- Configurate parametres in run.py
    ```python
        config = CVDConfig(
        symbol="BTC/USDT",
        target_tf="1h",
        since=datetime(2026, 7, 1),
        until=datetime(2026, 7, 20),
    )
    ```
- run run.py