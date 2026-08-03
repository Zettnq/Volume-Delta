from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class CVDConfig:
    symbol: str = "BTC/USDT"
    target_tf: str = "4h"
    since: datetime = datetime(2024, 1, 1, tzinfo=timezone.utc)  
    until: datetime = datetime(2024, 12, 31, tzinfo=timezone.utc)  
    exchange: str = "bybit"
    cache_dir: str = "cache"
    force_reload: bool = False
    
    method: str = "bvc" 
    bvc_ewma_span: int = 50