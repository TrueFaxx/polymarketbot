from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class RiskManager:
    def __init__(self, max_bet_size: float = 100.0, 
                 min_balance_threshold: float = 10.0,
                 daily_loss_limit: float = 0,
                 max_daily_trades: int = 0):
        self.max_bet_size = max_bet_size
        self.min_balance_threshold = min_balance_threshold
        self.daily_loss_limit = daily_loss_limit
        self.max_daily_trades = max_daily_trades
        
        self.daily_trades: List[Dict[str, Any]] = []
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        self.emergency_stop = False
    
    def _reset_daily_stats(self):
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_trades = []
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
    
    def check_pre_trade(self, size: float, price: float, balance: float) -> Dict[str, Any]:
        self._reset_daily_stats()
        
        if self.emergency_stop:
            return {
                'allowed': False,
                'reason': 'Emergency stop activated'
            }
        
        trade_cost = size * price
        
        if trade_cost > self.max_bet_size:
            return {
                'allowed': False,
                'reason': f'Trade cost ({trade_cost:.2f}) exceeds max bet size ({self.max_bet_size:.2f})'
            }
        
        if balance < trade_cost:
            return {
                'allowed': False,
                'reason': f'Insufficient balance ({balance:.2f}) for trade cost ({trade_cost:.2f})'
            }
        
        if balance - trade_cost < self.min_balance_threshold:
            return {
                'allowed': False,
                'reason': f'Trade would bring balance below minimum threshold ({self.min_balance_threshold:.2f})'
            }
        
        if self.max_daily_trades > 0 and len(self.daily_trades) >= self.max_daily_trades:
            return {
                'allowed': False,
                'reason': f'Daily trade limit reached ({self.max_daily_trades})'
            }
        
        if self.daily_loss_limit > 0 and self.daily_pnl < -self.daily_loss_limit:
            return {
                'allowed': False,
                'reason': f'Daily loss limit reached ({self.daily_loss_limit:.2f})'
            }
        
        return {
            'allowed': True,
            'reason': 'All risk checks passed'
        }
    
    def record_trade(self, trade_data: Dict[str, Any]):
        self._reset_daily_stats()
        
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.now().isoformat()
        
        self.daily_trades.append(trade_data)
        
        if 'pnl' in trade_data:
            self.daily_pnl += trade_data['pnl']
    
    def check_balance_threshold(self, balance: float) -> bool:
        return balance >= self.min_balance_threshold
    
    def activate_emergency_stop(self, reason: str = "Manual activation"):
        self.emergency_stop = True
        print(f"EMERGENCY STOP ACTIVATED: {reason}")
    
    def deactivate_emergency_stop(self):
        self.emergency_stop = False
        print("Emergency stop deactivated")
    
    def get_daily_stats(self) -> Dict[str, Any]:
        self._reset_daily_stats()
        
        return {
            'date': self.last_reset_date.isoformat(),
            'total_trades': len(self.daily_trades),
            'daily_pnl': self.daily_pnl,
            'trades_remaining': self.max_daily_trades - len(self.daily_trades) if self.max_daily_trades > 0 else 'unlimited',
            'loss_limit_remaining': self.daily_loss_limit + self.daily_pnl if self.daily_loss_limit > 0 else 'unlimited'
        }
    
    def get_risk_summary(self) -> Dict[str, Any]:
        return {
            'max_bet_size': self.max_bet_size,
            'min_balance_threshold': self.min_balance_threshold,
            'daily_loss_limit': self.daily_loss_limit,
            'max_daily_trades': self.max_daily_trades,
            'emergency_stop': self.emergency_stop,
            'daily_stats': self.get_daily_stats()
        }
