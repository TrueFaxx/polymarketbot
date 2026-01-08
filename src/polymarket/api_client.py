import time
from typing import Dict, Any, List, Optional
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.constants import POLYGON


class PolymarketAPIClient:
    def __init__(self, private_key: str, chain_id: int = POLYGON, 
                 host: str = "https://clob.polymarket.com"):
        self.private_key = private_key
        self.chain_id = chain_id
        self.host = host
        
        if private_key:
            try:
                self.client = ClobClient(
                    host=host,
                    key=private_key,
                    chain_id=chain_id
                )
            except Exception as e:
                print(f"Warning: Could not initialize CLOB client: {e}")
                self.client = None
        else:
            print("Warning: No private key provided, client not initialized")
            self.client = None
    
    def is_initialized(self) -> bool:
        return self.client is not None
    
    def get_markets(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            markets = self.client.get_markets(limit=limit, offset=offset)
            return markets
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []
    
    def get_market(self, condition_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        try:
            market = self.client.get_market(condition_id)
            return market
        except Exception as e:
            print(f"Error fetching market {condition_id}: {e}")
            return None
    
    def search_markets(self, query: str) -> List[Dict[str, Any]]:
        markets = self.get_markets(limit=100)
        
        query_lower = query.lower()
        matching_markets = [
            m for m in markets 
            if query_lower in m.get('question', '').lower() or 
               query_lower in m.get('description', '').lower()
        ]
        
        return matching_markets
    
    def get_market_price(self, token_id: str) -> Optional[float]:
        if not self.client:
            return None
        
        try:
            book = self.client.get_order_book(token_id)
            
            if book.get('bids') and book.get('asks'):
                best_bid = float(book['bids'][0]['price']) if book['bids'] else 0
                best_ask = float(book['asks'][0]['price']) if book['asks'] else 0
                
                if best_bid > 0 and best_ask > 0:
                    return (best_bid + best_ask) / 2
                elif best_bid > 0:
                    return best_bid
                elif best_ask > 0:
                    return best_ask
            
            return None
        except Exception as e:
            print(f"Error fetching market price for {token_id}: {e}")
            return None
    
    def get_balance(self) -> float:
        if not self.client:
            return 0.0
        
        try:
            balances = self.client.get_balances()
            usdc_balance = float(balances.get('USDC', 0))
            return usdc_balance
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0
    
    def get_positions(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            positions = self.client.get_positions()
            return positions
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []
    
    def place_market_order(self, token_id: str, side: str, size: float) -> Dict[str, Any]:
        if not self.client:
            return {
                'success': False,
                'error': 'Client not initialized'
            }
        
        try:
            order = OrderArgs(
                token_id=token_id,
                side=side.upper(),
                size=size,
                order_type=OrderType.MARKET
            )
            
            result = self.client.create_order(order)
            
            return {
                'success': True,
                'order_id': result.get('orderID'),
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def place_limit_order(self, token_id: str, side: str, size: float, 
                         price: float) -> Dict[str, Any]:
        if not self.client:
            return {
                'success': False,
                'error': 'Client not initialized'
            }
        
        try:
            order = OrderArgs(
                token_id=token_id,
                side=side.upper(),
                size=size,
                price=price,
                order_type=OrderType.LIMIT
            )
            
            result = self.client.create_order(order)
            
            return {
                'success': True,
                'order_id': result.get('orderID'),
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self, order_id: str) -> bool:
        if not self.client:
            return False
        
        try:
            self.client.cancel_order(order_id)
            return True
        except Exception as e:
            print(f"Error canceling order {order_id}: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        try:
            order = self.client.get_order(order_id)
            return order
        except Exception as e:
            print(f"Error fetching order status for {order_id}: {e}")
            return None

