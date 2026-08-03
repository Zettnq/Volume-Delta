import ccxt
import pandas as pd
import time

class Fetcher:
    def __init__(self, exchange_name="bybit"):
        print(f"⚙️ Initializing exchange: {exchange_name}...")
        self.exchange = getattr(ccxt, exchange_name)({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  
                'recvWindow': 10000,
            }
        })
        self.exchange.load_markets()
        print("✅ Markets loaded.")

    def fetch_ohlcv(self, symbol, timeframe='1m', since=None, until=None, limit_per_call=1000):
        # 1. Time convertation
        since_ms = int(since.timestamp() * 1000) if since else None
        until_ms = int(until.timestamp() * 1000) if until else None
        
        all_ohlcv = []
        current_since = since_ms
        
        print(f"\nStarting data fetch for {symbol} {timeframe}")
        if since:
            print(f"   From: {since} ({since_ms})")
        if until:
            print(f"   Until: {until} ({until_ms})")

        iteration = 0
        
        # 2. Pagination
        while True:
            iteration += 1
            try:
                # Bacth diagnostic
                dt_str = pd.to_datetime(current_since, unit='ms', utc=True).strftime('%Y-%m-%d %H:%M') if current_since else "None"
                print(f"   [Iter {iteration}] Fetching since: {dt_str}...")
                
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe, 
                    since=current_since, 
                    limit=limit_per_call
                )
                
                # Empty responce error protection
                if not ohlcv:
                    print("Empty response from exchange.")
                    break
                
                batch_start_ms = ohlcv[0][0]
                batch_end_ms = ohlcv[-1][0]
                
                print(f"Got {len(ohlcv)} candles: {pd.to_datetime(batch_start_ms, unit='ms', utc=True).strftime('%Y-%m-%d %H:%M')} -> {pd.to_datetime(batch_end_ms, unit='ms', utc=True).strftime('%Y-%m-%d %H:%M')}")
                
                all_ohlcv.extend(ohlcv)
                
                if ohlcv[-1][0] == current_since:
                    print("Data not advanced. Breaking loop to prevent infinite loop.")
                    break
                
                current_since = batch_end_ms + 1
                
                if until_ms and current_since >= until_ms:
                    print("Reached 'until' date.")
                    break
                
                # Exchnge rate limits
                time.sleep(self.exchange.rateLimit / 1000)
                
            except Exception as e:
                print(f"Error fetching data: {e}")
                time.sleep(5)  
                continue

        # Data Frame
        if not all_ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # UTC = True
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('datetime', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)
        
        df = df[~df.index.duplicated(keep='last')]
        
        print(f"\n✅ Total processed candles: {len(df)}")
        print(f"   Range: {df.index.min()} → {df.index.max()}")
        
        return df