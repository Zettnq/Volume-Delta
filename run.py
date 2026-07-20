from config import CVDConfig
from engine import VolumeDeltaEngine
from plotter import plot_volume_delta
from datetime import datetime

config = CVDConfig(
    symbol="BTC/USDT", # Symbol
    target_tf="1h", # Timeframe
    since=datetime(2026, 7, 1), # Strat date
    until=datetime(2026, 7, 20), # Stop date
)

engine = VolumeDeltaEngine(config)
df_delta = engine.run()
print(df_delta.head())
plot_volume_delta(df_delta, config.symbol, config.target_tf)

#Exanple exchange is BINANCE. You can select exchange in config.py