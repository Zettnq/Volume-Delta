from config import CVDConfig
from engine import VolumeDeltaEngine
from plotter import plot_volume_delta
from datetime import datetime

config = CVDConfig(
    symbol="BTC/USDT",
    target_tf="1h",
    since=datetime(2026, 7, 1),
    until=datetime(2026, 7, 20),
)

engine = VolumeDeltaEngine(config)
df_delta = engine.run()
print(df_delta.head())
plot_volume_delta(df_delta, config.symbol, config.target_tf)