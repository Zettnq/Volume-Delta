# Volume Delta Calculator

Tool for calculating Volume Delta from minute-level cryptocurrency exchange data. 
Supports two volume classification methods: **Candle Tick Rule** and **Bulk Volume Classification (BVC)**.

---

## Features

- Fetches minute candles via CCXT (any exchange)
- Volume Delta calculation using two methods
- Aggregation to any timeframe (`1h`, `4h`, `1d`, ...)
- CSV export of results
- Candlestick + delta histogram visualization

---

## Methods

### Candle Tick Rule (naive)
Candle volume is assigned to buys or sells based on candle direction:
- Close > Open → volume = buy
- Close < Open → volume = sell

### Bulk Volume Classification (BVC)
Based on Easley, López de Prado, O'Hara (2012). Uses the distribution of normalized price changes to probabilistically estimate the buy share:
```
ΔP = Close(t) - Close(t-1)
σ = EWMA(ΔP, span)
z = ΔP / σ
P_buy = CDF(z)
Delta = Volume × (2 × P_buy - 1)
```

---

### Installation

```bash
git clone https://github.com/Zettnq/Volume-Delta.git
cd Volume-Delta
pip install -r requirements.txt 
```

---

### Usage 

Configure parameters in run.py

Run:
```bash
python run.py
```
Results are saved to the output/ folder. 

---

### Structure 
```
Volume-Delta/
├── run.py          # Entry point
├── config.py       # Configuration
├── engine.py       # Core logic
├── fetcher.py      # Data fetching
├── calculators.py  # Delta calculation methods
├── plotter.py      # Visualization
├── requirements.txt
└── LICENSE         # MIT
```
--- 

### License & disclaimer

MIT — see here: [`LICENSE`](LICENSE). 
**Research only. Not investment advice. Nothing here constitutes a recommendation to buy or sell any asset.**

© 2026 Zettnq · MIT License
