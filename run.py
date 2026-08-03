from config import CVDConfig
from engine import VolumeDeltaEngine
from plotter import plot_volume_delta
from datetime import datetime, timezone  

config = CVDConfig(
    symbol="BTC/USDT",
    target_tf="4h",
    since=datetime(2026, 7, 1, tzinfo=timezone.utc),  
    until=datetime(2026, 8, 3, tzinfo=timezone.utc),  
    method="bvc",
    bvc_ewma_span=50,
    force_reload=True
)

engine = VolumeDeltaEngine(config)
df_delta = engine.run()

if not df_delta.empty:
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print(f"Method:        {config.method.upper()}")
    print(f"Target TF:     {config.target_tf}")
    print(f"Requested:     {config.since} → {config.until}")
    print(f"Actual data:   {df_delta.index.min()} → {df_delta.index.max()}")
    print(f"Total candles: {len(df_delta)}")
    print(f"Delta range:   {df_delta['volume_delta'].min():.2f} → {df_delta['volume_delta'].max():.2f}")
    print(f"Delta sum:     {df_delta['volume_delta'].sum():.2f}")
    print("=" * 60 + "\n")

    print(df_delta.head(10))
    print("...")
    print(df_delta.tail(10))

    plot_volume_delta(df_delta, config.symbol, config.target_tf, config.method)
else:
    print("No data returned.")