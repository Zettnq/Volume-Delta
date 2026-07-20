import ccxt
import pandas as pd
import time

class Fetcher:
    def __init__(self, exchange_name="binance"):
        self.exchange = getattr(ccxt, exchange_name)({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })

    def fetch_ohlcv(self, symbol, timeframe='1m', since=None, until=None, limit_per_call=1000):
        since_ms = int(since.timestamp() * 1000) if since else None
        until_ms = int(until.timestamp() * 1000) if until else None
        all_ohlcv = []
        current_since = since_ms

        while True:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, timeframe,
                    since=current_since,
                    limit=limit_per_call,
                    params={"until": until_ms} if until_ms else {}
                )
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                print(f"Received {len(ohlcv)} candles, total: {len(all_ohlcv)}")
                current_since = ohlcv[-1][0] + 1
                if until_ms and current_since >= until_ms:
                    print("Completed")
                    break
                time.sleep(self.exchange.rateLimit / 1000)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(2)
                break

        if not all_ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)

        print(f"Total candles: {len(df)} from {df.index.min()} to {df.index.max()}")
        return df


        return df