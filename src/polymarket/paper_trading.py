import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


class PaperTradingAccount:
    def __init__(self, initial_balance: float = 10000.0, track_pnl: bool = True, 
                 data_file: str = "paper_trades.json"):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.track_pnl = track_pnl
        self.data_file = data_file
        
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trades: List[Dict[str, Any]] = []
        self.total_pnl = 0.0
        
        self._load_data()
    
    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.balance = data.get('balance', self.initial_balance)
                    self.positions = data.get('positions', {})
                    self.trades = data.get('trades', [])
                    self.total_pnl = data.get('total_pnl', 0.0)
            except Exception as e:
                print(f"Warning: Could not load paper trading data: {e}")
    
    def _save_data(self):
        try:
            data = {
                'initial_balance': self.initial_balance,
                'balance': self.balance,
                'positions': self.positions,
                'trades': self.trades,
                'total_pnl': self.total_pnl,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save paper trading data: {e}")
    
    def get_balance(self) -> float:
        return self.balance
    
    def get_pnl(self) -> float:
        return self.total_pnl
    
    def get_position(self, market_id: str) -> Optional[Dict[str, Any]]:
        return self.positions.get(market_id)
    
    def place_order(self, market_id: str, side: str, size: float, price: float,
                   market_name: str = "") -> Dict[str, Any]:
        cost = size * price
        
        if side.lower() == 'buy':
            if cost > self.balance:
                return {
                    'success': False,
                    'error': 'Insufficient balance',
                    'balance': self.balance,
                    'required': cost
                }
            
            self.balance -= cost
            
            if market_id in self.positions:
                pos = self.positions[market_id]
                total_shares = pos['size'] + size
                avg_price = ((pos['size'] * pos['avg_price']) + (size * price)) / total_shares
                pos['size'] = total_shares
                pos['avg_price'] = avg_price
            else:
                self.positions[market_id] = {
                    'market_id': market_id,
                    'market_name': market_name,
                    'side': 'long',
                    'size': size,
                    'avg_price': price,
                    'entry_time': datetime.now().isoformat()
                }
        
        elif side.lower() == 'sell':
            if market_id not in self.positions:
                return {
                    'success': False,
                    'error': 'No position to sell'
                }
            
            pos = self.positions[market_id]
            if pos['size'] < size:
                return {
                    'success': False,
                    'error': f'Insufficient position size. Have {pos["size"]}, trying to sell {size}'
                }
            
            pnl = size * (price - pos['avg_price'])
            self.total_pnl += pnl
            
            self.balance += cost
            
            pos['size'] -= size
            if pos['size'] <= 0:
                del self.positions[market_id]
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'market_id': market_id,
            'market_name': market_name,
            'side': side,
            'size': size,
            'price': price,
            'cost': cost,
            'balance_after': self.balance
        }
        self.trades.append(trade)
        
        self._save_data()
        
        return {
            'success': True,
            'trade': trade,
            'balance': self.balance,
            'pnl': self.total_pnl
        }
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_pnl': self.total_pnl,
            'total_trades': len(self.trades),
            'open_positions': len(self.positions),
            'positions': self.positions
        }
    
    def reset(self):
        self.balance = self.initial_balance
        self.positions = {}
        self.trades = []
        self.total_pnl = 0.0
        self._save_data()
