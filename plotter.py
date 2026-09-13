import mplfinance as mpf
import pandas as pd

def plot_volume_delta(df, symbol, target_tf, method="bvc"):
    if df.empty:
        print("Dataframe is empty")
        return

    x_start = df.index[0]
    x_end = df.index[-1]

    delta_colors = ['g' if v >= 0 else 'r' for v in df['volume_delta']]

    apds = [
        mpf.make_addplot(
            df['volume_delta'],
            panel=2,
            color=delta_colors,
            type='bar',
            ylabel='Delta'
        )
    ]

    fig, axes = mpf.plot(
        df,
        type='candle',
        style='charles',
        volume=True,
        title=f'\n{symbol} {target_tf} Volume Delta ({method.upper()})',
        addplot=apds,
        panel_ratios=(3, 1, 1),
        figsize=(16, 9),          
        xlim=(x_start, x_end),    
        tight_layout=True,
        returnfig=True,           
        datetime_format='%Y-%m-%d %H:%M',  
        xrotation=20              
    )

    axes[0].set_xlabel(
        f'Period: {x_start.strftime("%Y-%m-%d %H:%M")} → {x_end.strftime("%Y-%m-%d %H:%M")}  |  Candles: {len(df)}',
        fontsize=10
    )

    mpf.show()