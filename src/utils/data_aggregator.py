import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class BitcoinPriceAggregator:
    def __init__(self, exchange: str = 'binance', symbol: str = 'BTC/USDT',
                 api_key: str = '', api_secret: str = ''):
        self.exchange_name = exchange
        self.symbol = symbol
        
        try:
            exchange_class = getattr(ccxt, exchange)
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True
            })
        except Exception as e:
            print(f"Error initializing exchange {exchange}: {e}")
            self.exchange = None
        
        self.historical_data = pd.DataFrame()
        self.last_update = None
    
    def fetch_ohlcv(self, timeframe: str = '15m', limit: int = 100) -> Optional[pd.DataFrame]:
        if not self.exchange:
            return None
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            self.historical_data = df
            self.last_update = datetime.now()
            
            return df
        
        except Exception as e:
            print(f"Error fetching OHLCV data: {e}")
            return None
    
    def fetch_current_price(self) -> Optional[float]:
        if not self.exchange:
            return None
        
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching current price: {e}")
            return None
    
    def get_15min_candles(self, count: int = 100) -> Optional[pd.DataFrame]:
        return self.fetch_ohlcv(timeframe='15m', limit=count)
    
    def aggregate_to_interval(self, df: pd.DataFrame, interval: str = '15T') -> pd.DataFrame:
        if df.empty:
            return df
        
        aggregated = df.resample(interval).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        aggregated.dropna(inplace=True)
        
        return aggregated
    
    def get_latest_candle(self) -> Optional[Dict[str, Any]]:
        if self.historical_data.empty:
            return None
        
        latest = self.historical_data.iloc[-1]
        
        return {
            'timestamp': latest.name,
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'close': latest['close'],
            'volume': latest['volume']
        }
    
    def get_price_change(self, periods: int = 1) -> Optional[float]:
        if self.historical_data.empty or len(self.historical_data) < periods + 1:
            return None
        
        current_price = self.historical_data['close'].iloc[-1]
        past_price = self.historical_data['close'].iloc[-(periods + 1)]
        
        change = ((current_price - past_price) / past_price) * 100
        
        return change
    
    def is_data_fresh(self, max_age_minutes: int = 20) -> bool:
        if self.last_update is None:
            return False
        
        age = datetime.now() - self.last_update
        return age < timedelta(minutes=max_age_minutes)
    
    def update_data(self, force: bool = False) -> bool:
        if force or not self.is_data_fresh():
            df = self.get_15min_candles()
            return df is not None
        
        return True
