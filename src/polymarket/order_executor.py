from typing import Dict, Any, Optional
from .api_client import PolymarketAPIClient
from .paper_trading import PaperTradingAccount


class OrderExecutor:
    def __init__(self, api_client: PolymarketAPIClient, 
                 paper_trading: bool = True,
                 paper_account: Optional[PaperTradingAccount] = None):
        self.api_client = api_client
        self.paper_trading = paper_trading
        
        if paper_trading:
            self.paper_account = paper_account or PaperTradingAccount()
        else:
            self.paper_account = None
    
    def validate_order(self, token_id: str, side: str, size: float, 
                      price: Optional[float] = None) -> Dict[str, Any]:
        errors = []
        
        if not token_id or not isinstance(token_id, str):
            errors.append("Invalid token_id")
        
        if side.lower() not in ['buy', 'sell']:
            errors.append("Invalid side (must be 'buy' or 'sell')")
        
        if size <= 0:
            errors.append("Size must be greater than 0")
        
        if price is not None:
            if price <= 0 or price > 1:
                errors.append("Price must be between 0 and 1")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def execute_market_order(self, token_id: str, side: str, size: float,
                           market_id: str = "", market_name: str = "") -> Dict[str, Any]:
        validation = self.validate_order(token_id, side, size)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Validation failed: {', '.join(validation['errors'])}",
                'paper_trade': self.paper_trading
            }
        
        if self.paper_trading:
            price = self.api_client.get_market_price(token_id) if self.api_client.is_initialized() else 0.5
            if price is None:
                price = 0.5
            
            result = self.paper_account.place_order(
                market_id=market_id or token_id,
                side=side,
                size=size,
                price=price,
                market_name=market_name
            )
            
            if result['success']:
                return {
                    'success': True,
                    'paper_trade': True,
                    'order_id': f"paper_{result['trade']['timestamp']}",
                    'price': price,
                    'size': size,
                    'balance': result['balance'],
                    'pnl': result['pnl']
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'paper_trade': True
                }
        
        else:
            if not self.api_client.is_initialized():
                return {
                    'success': False,
                    'error': 'API client not initialized',
                    'paper_trade': False
                }
            
            result = self.api_client.place_market_order(token_id, side, size)
            
            if result['success']:
                return {
                    'success': True,
                    'paper_trade': False,
                    'order_id': result['order_id'],
                    'result': result['result']
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'paper_trade': False
                }
    
    def execute_limit_order(self, token_id: str, side: str, size: float, price: float,
                          market_id: str = "", market_name: str = "") -> Dict[str, Any]:
        validation = self.validate_order(token_id, side, size, price)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Validation failed: {', '.join(validation['errors'])}",
                'paper_trade': self.paper_trading
            }
        
        if self.paper_trading:
            result = self.paper_account.place_order(
                market_id=market_id or token_id,
                side=side,
                size=size,
                price=price,
                market_name=market_name
            )
            
            if result['success']:
                return {
                    'success': True,
                    'paper_trade': True,
                    'order_id': f"paper_{result['trade']['timestamp']}",
                    'price': price,
                    'size': size,
                    'balance': result['balance'],
                    'pnl': result['pnl']
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'paper_trade': True
                }
        
        else:
            if not self.api_client.is_initialized():
                return {
                    'success': False,
                    'error': 'API client not initialized',
                    'paper_trade': False
                }
            
            result = self.api_client.place_limit_order(token_id, side, size, price)
            
            if result['success']:
                return {
                    'success': True,
                    'paper_trade': False,
                    'order_id': result['order_id'],
                    'result': result['result']
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'paper_trade': False
                }
    
    def get_balance(self) -> float:
        if self.paper_trading:
            return self.paper_account.get_balance()
        else:
            if self.api_client.is_initialized():
                return self.api_client.get_balance()
            return 0.0
    
    def get_pnl(self) -> float:
        if self.paper_trading and self.paper_account:
            return self.paper_account.get_pnl()
        return 0.0
    
    def get_positions(self) -> Dict[str, Any]:
        if self.paper_trading:
            return self.paper_account.positions
        else:
            if self.api_client.is_initialized():
                return self.api_client.get_positions()
            return {}
    
    def get_account_summary(self) -> Dict[str, Any]:
        if self.paper_trading:
            return self.paper_account.get_summary()
        else:
            return {
                'balance': self.get_balance(),
                'positions': self.get_positions()
            }
