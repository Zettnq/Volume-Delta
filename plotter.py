import mplfinance as mpf
import pandas as pd

def plot_volume_delta(df, symbol, target_tf):
    # Volume delta chart
    apds = [
        mpf.make_addplot(df['volume_delta'], panel=2, color='g', type='bar', ylabel='Delta')
    ]
    # Price chart
    mpf.plot(df, type='candle', style='charles', volume=True,
             title=f'{symbol} {target_tf} with Volume Delta',
             addplot=apds, panel_ratios=(2, 1))