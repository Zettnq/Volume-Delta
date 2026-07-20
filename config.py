from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class CVDConfig:
    symbol: str = "BTC/USDT"
    target_tf: str = "4h"          
    since: datetime = datetime(2024, 1, 1)
    until: datetime = datetime(2024, 12, 31)
    exchange: str = "binance"
    cache_dir: str = "cache"       # cache 