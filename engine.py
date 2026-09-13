import pandas as pd
from pathlib import Path
from config import CVDConfig
from fetcher import Fetcher
from calculators import CandleRuleCalculator, BVCCalculator

class VolumeDeltaEngine:
    def __init__(self, config: CVDConfig):
        self.config = config
        self.fetcher = Fetcher(config.exchange)
        
        if self.config.method == "bvc":
            self.calculator = BVCCalculator(ewma_span=self.config.bvc_ewma_span)
        elif self.config.method == "candle":
            self.calculator = CandleRuleCalculator()
        else:
            raise ValueError(f"Неизвестный метод: {self.config.method}")

    def _cached_minute_data(self):
        if self.config.force_reload:
            print("⚠️ Force reload enabled - ignoring cache")
            return None
            
        cache_path = Path(self.config.cache_dir) / f"{self.config.symbol.replace('/', '')}_1m.pkl"
        if cache_path.exists():
            print(f"Loading cached minute data from {cache_path}...")
            df = pd.read_pickle(cache_path)
            
            # Cache date check
            cache_start = df.index.min()
            cache_end = df.index.max()
            
            if cache_start <= self.config.since and cache_end >= self.config.until:
                print(f"✓ Cache covers requested period: {cache_start} → {cache_end}")
                return df
            else:
                print(f"⚠️ Cache does NOT cover requested period!")
                print(f"   Cache:    {cache_start} → {cache_end}")
                print(f"   Required: {self.config.since} → {self.config.until}")
                print(f"   Reloading data...")
                return None
        return None

    def _save_minute_data(self, df):
        cache_dir = Path(self.config.cache_dir)
        cache_dir.mkdir(exist_ok=True)
        cache_path = cache_dir / f"{self.config.symbol.replace('/', '')}_1m.pkl"
        df.to_pickle(cache_path)
        print(f"✓ Minute data saved to {cache_path}")
        print(f"  Range: {df.index.min()} → {df.index.max()}")
        print(f"  Total candles: {len(df)}")

    def run(self):
        # Fetch 1-minute data
        df_1m = self._cached_minute_data()
        if df_1m is None:
            print(f"\nFetching data from {self.config.exchange}...")
            df_1m = self.fetcher.fetch_ohlcv(
                self.config.symbol, '1m',
                since=self.config.since,
                until=self.config.until
            )
            if df_1m.empty:
                print("No data received from exchange")
                return pd.DataFrame()
            self._save_minute_data(df_1m)
        
        df_1m = df_1m[(df_1m.index >= self.config.since) & (df_1m.index <= self.config.until)]
        
        if df_1m.empty:
            print("No data in requested range after filtering")
            return pd.DataFrame()

        # 2. Delta
        print(f"\nCalculating Volume Delta using '{self.config.method.upper()}' method...")
        df_1m['volume_delta'] = self.calculator.calculate(df_1m)

        # 3. Aggregation to target timeframe
        rule = self.config.target_tf
        df_target = df_1m.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'volume_delta': 'sum'
        }).dropna()

        return df_target

    def export_csv(self, df: pd.DataFrame, custom_filename: str = None) -> str:
        """
        Export OHLCV + VD to CSV.
        
        Args:
            df: DataFrame with volume delta
            custom_filename: your filename (without .csv)
            
        Returns:
            Path to file
        """
        if df.empty:
            print("DataFrame is empty")
            return None
            
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        if custom_filename:
            filename = f"{custom_filename}.csv"
        else:
            filename = (f"{self.config.symbol.replace('/', '_')}_"
                       f"{self.config.target_tf}_"
                       f"{self.config.method}_"
                       f"{self.config.since.strftime('%Y%m%d')}_"
                       f"{self.config.until.strftime('%Y%m%d')}.csv")
        
        output_path = output_dir / filename
        
        export_df = df.copy()
        
        export_df = export_df.reset_index()
        export_df.rename(columns={'datetime': 'timestamp'}, inplace=True)
        
        cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volume_delta']
        export_df = export_df[cols]
        
        export_df['timestamp'] = export_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        export_df.to_csv(output_path, index=False)
        
        print(f"\n✓ CSV exported: {output_path}")
        print(f"  Rows: {len(export_df)}")
        print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
        
        return str(output_path)