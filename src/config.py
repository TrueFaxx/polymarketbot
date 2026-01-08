import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        load_dotenv()
        
        with open(config_path, 'r') as f:
            self.config: Dict[str, Any] = yaml.safe_load(f)
        
        self.env = {
            'polymarket_private_key': os.getenv('POLYMARKET_PRIVATE_KEY', ''),
            'polymarket_api_key': os.getenv('POLYMARKET_API_KEY', ''),
            'polymarket_api_secret': os.getenv('POLYMARKET_API_SECRET', ''),
            'polymarket_passphrase': os.getenv('POLYMARKET_PASSPHRASE', ''),
            'binance_api_key': os.getenv('BINANCE_API_KEY', ''),
            'binance_api_secret': os.getenv('BINANCE_API_SECRET', ''),
            'coinbase_api_key': os.getenv('COINBASE_API_KEY', ''),
            'coinbase_api_secret': os.getenv('COINBASE_API_SECRET', ''),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value, supports nested keys with dots (e.g., 'risk_management.max_bet_size')"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: str = '') -> str:
        return self.env.get(key, default)
    
    @property
    def mode(self) -> str:
        return self.config.get('mode', 'trend_analysis')
    
    @property
    def paper_trading(self) -> bool:
        return self.config.get('paper_trading', True)
    
    @property
    def paper_trading_settings(self) -> Dict[str, Any]:
        return self.config.get('paper_trading_settings', {
            'initial_balance': 10000.0,
            'track_pnl': True
        })
    
    @property
    def trend_analysis_config(self) -> Dict[str, Any]:
        return self.config.get('trend_analysis', {})
    
    @property
    def copy_trading_config(self) -> Dict[str, Any]:
        return self.config.get('copy_trading', {})
    
    @property
    def risk_config(self) -> Dict[str, Any]:
        return self.config.get('risk_management', {})
    
    @property
    def polymarket_config(self) -> Dict[str, Any]:
        return self.config.get('polymarket', {})
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        return self.config.get('logging', {})

