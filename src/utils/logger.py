import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json


class TradingLogger:
    def __init__(self, log_dir: str = "logs", level: str = "INFO", console_output: bool = True):
        self.log_dir = log_dir
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.console_output = console_output
        
        os.makedirs(log_dir, exist_ok=True)
        
        self.logger = logging.getLogger("PolymarketBot")
        self.logger.setLevel(self.level)
        self.logger.handlers.clear()
        
        log_filename = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(self.level)
        
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.level)
            
            console_format = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
        
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        self.trade_log_file = os.path.join(log_dir, f"trades_{datetime.now().strftime('%Y%m%d')}.jsonl")
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        self.logger.error(message, exc_info=exc_info)
    
    def log_trade(self, trade_data: Dict[str, Any]):
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.now().isoformat()
        
        trade_type = "PAPER" if trade_data.get('paper_trade', False) else "LIVE"
        log_msg = (
            f"{trade_type} TRADE - {trade_data.get('mode', 'unknown').upper()} - "
            f"{trade_data.get('side', 'unknown').upper()} {trade_data.get('size', 0)} "
            f"@ {trade_data.get('price', 0)} - Market: {trade_data.get('market_name', trade_data.get('market', 'unknown'))} - "
            f"Result: {trade_data.get('result', 'unknown')}"
        )
        
        if trade_data.get('result') == 'success':
            self.logger.info(log_msg)
        else:
            self.logger.error(log_msg)
        
        try:
            with open(self.trade_log_file, 'a') as f:
                f.write(json.dumps(trade_data) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to trade log file: {e}")
    
    def log_signal(self, signal_data: Dict[str, Any]):
        if 'timestamp' not in signal_data:
            signal_data['timestamp'] = datetime.now().isoformat()
        
        log_msg = (
            f"SIGNAL - {signal_data.get('mode', 'unknown').upper()} - "
            f"{signal_data.get('signal', 'unknown').upper()} - "
            f"Reason: {signal_data.get('reason', 'N/A')}"
        )
        
        self.logger.info(log_msg)
    
    def log_balance(self, balance_data: Dict[str, Any]):
        if 'timestamp' not in balance_data:
            balance_data['timestamp'] = datetime.now().isoformat()
        
        trade_type = "PAPER" if balance_data.get('paper_trade', False) else "LIVE"
        pnl_str = f" | PnL: {balance_data.get('pnl', 0):.2f}" if 'pnl' in balance_data else ""
        
        log_msg = f"{trade_type} BALANCE - {balance_data.get('balance', 0):.2f} USDC{pnl_str}"
        self.logger.info(log_msg)
