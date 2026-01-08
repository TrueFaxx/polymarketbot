import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator

from ..utils.data_aggregator import BitcoinPriceAggregator
from ..polymarket.order_executor import OrderExecutor
from ..risk.risk_manager import RiskManager
from ..utils.logger import TradingLogger


class TrendAnalysisMode:
    def __init__(self, config: Dict[str, Any], order_executor: OrderExecutor,
                 risk_manager: RiskManager, logger: TradingLogger):
        self.config = config
        self.order_executor = order_executor
        self.risk_manager = risk_manager
        self.logger = logger
        
        self.interval = config.get('interval', 15)
        self.indicators_config = config.get('indicators', {})
        self.signals_config = config.get('signals', {})
        self.market_id = config.get('market_id', '')
        self.exchange = config.get('exchange', 'binance')
        self.symbol = config.get('symbol', 'BTC/USDT')
        
        self.price_aggregator = BitcoinPriceAggregator(
            exchange=self.exchange,
            symbol=self.symbol
        )
        
        self.last_signal = None
        self.last_signal_time = None
        self.running = False
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or len(df) < 30:
            return {}
        
        ema_short = self.indicators_config.get('ema_short', 9)
        ema_long = self.indicators_config.get('ema_long', 21)
        rsi_period = self.indicators_config.get('rsi_period', 14)
        macd_fast = self.indicators_config.get('macd_fast', 12)
        macd_slow = self.indicators_config.get('macd_slow', 26)
        macd_signal = self.indicators_config.get('macd_signal', 9)
        
        try:
            ema_short_indicator = EMAIndicator(close=df['close'], window=ema_short)
            ema_long_indicator = EMAIndicator(close=df['close'], window=ema_long)
            
            ema_short_values = ema_short_indicator.ema_indicator()
            ema_long_values = ema_long_indicator.ema_indicator()
            
            rsi_indicator = RSIIndicator(close=df['close'], window=rsi_period)
            rsi_values = rsi_indicator.rsi()
            
            macd_indicator = MACD(
                close=df['close'],
                window_fast=macd_fast,
                window_slow=macd_slow,
                window_sign=macd_signal
            )
            macd_values = macd_indicator.macd()
            macd_signal_values = macd_indicator.macd_signal()
            macd_diff = macd_indicator.macd_diff()
            
            indicators = {
                'ema_short': ema_short_values.iloc[-1],
                'ema_long': ema_long_values.iloc[-1],
                'ema_short_prev': ema_short_values.iloc[-2] if len(ema_short_values) > 1 else None,
                'ema_long_prev': ema_long_values.iloc[-2] if len(ema_long_values) > 1 else None,
                'rsi': rsi_values.iloc[-1],
                'macd': macd_values.iloc[-1],
                'macd_signal': macd_signal_values.iloc[-1],
                'macd_diff': macd_diff.iloc[-1],
                'current_price': df['close'].iloc[-1]
            }
            
            return indicators
        
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}", exc_info=True)
            return {}
    
    def generate_signal(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        if not indicators:
            return {'signal': 'hold', 'reason': 'No indicators available'}
        
        rsi_overbought = self.signals_config.get('rsi_overbought', 70)
        rsi_oversold = self.signals_config.get('rsi_oversold', 30)
        
        ema_short = indicators.get('ema_short')
        ema_long = indicators.get('ema_long')
        ema_short_prev = indicators.get('ema_short_prev')
        ema_long_prev = indicators.get('ema_long_prev')
        rsi = indicators.get('rsi')
        macd_diff = indicators.get('macd_diff')
        
        bullish_crossover = False
        bearish_crossover = False
        
        if ema_short and ema_long and ema_short_prev and ema_long_prev:
            if ema_short_prev <= ema_long_prev and ema_short > ema_long:
                bullish_crossover = True
            
            if ema_short_prev >= ema_long_prev and ema_short < ema_long:
                bearish_crossover = True
        
        if bullish_crossover and rsi < rsi_overbought:
            return {
                'signal': 'buy',
                'reason': f'Bullish EMA crossover (EMA{self.indicators_config.get("ema_short", 9)} > EMA{self.indicators_config.get("ema_long", 21)}) and RSI {rsi:.2f} < {rsi_overbought}',
                'indicators': indicators
            }
        
        if bearish_crossover and rsi > rsi_oversold:
            return {
                'signal': 'sell',
                'reason': f'Bearish EMA crossover (EMA{self.indicators_config.get("ema_short", 9)} < EMA{self.indicators_config.get("ema_long", 21)}) and RSI {rsi:.2f} > {rsi_oversold}',
                'indicators': indicators
            }
        
        return {
            'signal': 'hold',
            'reason': f'No clear signal (EMA short: {ema_short:.2f}, EMA long: {ema_long:.2f}, RSI: {rsi:.2f})',
            'indicators': indicators
        }
    
    def execute_signal(self, signal: Dict[str, Any]) -> bool:
        signal_type = signal['signal']
        
        if signal_type == 'hold':
            return False
        
        if signal_type == self.last_signal:
            self.logger.debug(f"Skipping duplicate {signal_type} signal")
            return False
        
        balance = self.order_executor.get_balance()
        
        max_bet = self.risk_manager.max_bet_size
        price = 0.5
        size = max_bet / price
        
        risk_check = self.risk_manager.check_pre_trade(size, price, balance)
        
        if not risk_check['allowed']:
            self.logger.warning(f"Trade blocked by risk manager: {risk_check['reason']}")
            return False
        
        token_id = self.market_id
        side = 'buy' if signal_type == 'buy' else 'sell'
        
        self.logger.info(f"Executing {signal_type.upper()} signal: {signal['reason']}")
        
        result = self.order_executor.execute_market_order(
            token_id=token_id or 'BTC_15MIN_UP',
            side=side,
            size=size,
            market_id=self.market_id or 'btc_15min',
            market_name='Bitcoin 15min Up/Down'
        )
        
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'trend_analysis',
            'market': self.market_id or 'btc_15min',
            'market_name': 'Bitcoin 15min Up/Down',
            'side': side,
            'size': size,
            'price': result.get('price', price),
            'result': 'success' if result['success'] else 'failed',
            'paper_trade': result.get('paper_trade', False),
            'reason': signal['reason'],
            'indicators': signal.get('indicators', {})
        }
        
        if not result['success']:
            trade_data['error'] = result.get('error', 'Unknown error')
        
        self.logger.log_trade(trade_data)
        
        if result['success']:
            self.risk_manager.record_trade(trade_data)
            self.last_signal = signal_type
            self.last_signal_time = datetime.now()
        
        return result['success']
    
    async def run(self):
        self.running = True
        self.logger.info("Starting Bitcoin Trend Analysis mode")
        self.logger.info(f"Interval: {self.interval} minutes")
        self.logger.info(f"Exchange: {self.exchange}, Symbol: {self.symbol}")
        
        balance = self.order_executor.get_balance()
        self.logger.log_balance({
            'balance': balance,
            'paper_trade': self.order_executor.paper_trading
        })
        
        while self.running:
            try:
                self.logger.debug("Fetching Bitcoin price data...")
                df = self.price_aggregator.get_15min_candles(count=100)
                
                if df is None or df.empty:
                    self.logger.warning("Failed to fetch price data")
                    await asyncio.sleep(60)
                    continue
                
                self.logger.debug("Calculating technical indicators...")
                indicators = self.calculate_indicators(df)
                
                if not indicators:
                    self.logger.warning("Failed to calculate indicators")
                    await asyncio.sleep(60)
                    continue
                
                signal = self.generate_signal(indicators)
                
                self.logger.log_signal({
                    'mode': 'trend_analysis',
                    'signal': signal['signal'],
                    'reason': signal['reason']
                })
                
                if signal['signal'] != 'hold':
                    self.execute_signal(signal)
                
                self.logger.debug(f"Waiting {self.interval} minutes until next analysis...")
                await asyncio.sleep(self.interval * 60)
            
            except Exception as e:
                self.logger.error(f"Error in trend analysis loop: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        self.logger.info("Trend analysis mode stopped")
    
    def stop(self):
        self.running = False
