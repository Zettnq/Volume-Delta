import pandas as pd
from pathlib import Path
from config import CVDConfig
from fetcher import Fetcher

class VolumeDeltaEngine:
    def __init__(self, config: CVDConfig):
        self.config = config
        self.fetcher = Fetcher(config.exchange)

    def _cached_minute_data(self):
        cache_path = Path(self.config.cache_dir) / f"{self.config.symbol.replace('/', '')}_1m.pkl"
        if cache_path.exists():
            print("Loading cached minute data...")
            return pd.read_pickle(cache_path)
        return None

    def _save_minute_data(self, df):
        cache_dir = Path(self.config.cache_dir)
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / f"{self.config.symbol.replace('/', '')}_1m.pkl"
        df.to_pickle(cache_path)
        print(f"Minute data saved to {cache_path}")

    def run(self):
        # 1. Загрузить/получить минутные данные
        df_1m = self._cached_minute_data()
        if df_1m is None:
            df_1m = self.fetcher.fetch_ohlcv(
                self.config.symbol, '1m',
                since=self.config.since,
                until=self.config.until
            )
            if df_1m.empty:
                return pd.DataFrame()
            self._save_minute_data(df_1m)

        # 2. Вычислить дельту на каждом минутном баре
        direction = ((df_1m['close'] > df_1m['open']).astype(int) -
                     (df_1m['close'] < df_1m['open']).astype(int))
        df_1m['volume_delta'] = df_1m['volume'] * direction

        # 3. Частоту берём как есть из конфига (например, '1h', '4h', '1d')
        rule = self.config.target_tf

        # 4. Агрегация в целевой ТФ
        df_target = df_1m.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'volume_delta': 'sum'
        }).dropna()

        return df_target