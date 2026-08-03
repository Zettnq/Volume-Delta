import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from scipy.stats import norm

class BaseCalculator(ABC):
    """Abstract base class"""
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        pass

class CandleRuleCalculator(BaseCalculator):
    """Candle tick rule method"""
    
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        direction = ((df['close'] > df['open']).astype(int) - 
                     (df['close'] < df['open']).astype(int))
        return df['volume'] * direction

class BVCCalculator(BaseCalculator):
    """
    Adaptive Bulk Volume Classification 
    Use CDF of normal distribution for propabilities
    """
    
    def __init__(self, ewma_span: int = 50):
        self.ewma_span = ewma_span

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        # 1. Close price to close price
        delta_p = df['close'].diff().fillna(0)
        
        # 2. EWMA volatility
        sigma = delta_p.ewm(span=self.ewma_span, adjust=False).std()
        
        sigma = sigma.replace(0, np.nan).fillna(np.inf)
        
        # 3. Z-score 
        z = (delta_p / sigma).fillna(0)
        
        # 4. Propability of buy using Cumulative Distuibution Function
        prob_buy = norm.cdf(z)
        
        # 5. Delta calculating
        # V_buy = V * prob_buy, V_sell = V * (1 - prob_buy)
        # Delta = V_buy - V_sell = V * (2 * prob_buy - 1)
        volume_delta = df['volume'] * (2 * prob_buy - 1)
        
        return volume_delta