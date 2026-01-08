import asyncio
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.utils.logger import TradingLogger
from src.polymarket.api_client import PolymarketAPIClient
from src.polymarket.paper_trading import PaperTradingAccount
from src.polymarket.order_executor import OrderExecutor
from src.risk.risk_manager import RiskManager
from src.modes.trend_analysis import TrendAnalysisMode
from src.modes.copy_trading import CopyTradingMode


class PolymarketBot:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config(config_path)
        
        log_config = self.config.logging_config
        self.logger = TradingLogger(
            log_dir=log_config.get('log_dir', 'logs'),
            level=log_config.get('level', 'INFO'),
            console_output=log_config.get('console_output', True)
        )
        
        self.logger.info("=" * 60)
        self.logger.info("Polymarket Trading Bot Starting")
        self.logger.info("=" * 60)
        
        private_key = self.config.get_env('polymarket_private_key')
        polymarket_config = self.config.polymarket_config
        
        self.api_client = PolymarketAPIClient(
            private_key=private_key,
            chain_id=polymarket_config.get('chain_id', 137),
            host=polymarket_config.get('clob_url', 'https://clob.polymarket.com')
        )
        
        paper_trading = self.config.paper_trading
        paper_account = None
        
        if paper_trading:
            self.logger.info("Paper trading mode enabled")
            paper_settings = self.config.paper_trading_settings
            paper_account = PaperTradingAccount(
                initial_balance=paper_settings.get('initial_balance', 10000.0),
                track_pnl=paper_settings.get('track_pnl', True)
            )
        else:
            self.logger.warning("LIVE TRADING MODE - Real money will be used!")
        
        self.order_executor = OrderExecutor(
            api_client=self.api_client,
            paper_trading=paper_trading,
            paper_account=paper_account
        )
        
        risk_config = self.config.risk_config
        self.risk_manager = RiskManager(
            max_bet_size=risk_config.get('max_bet_size', 100.0),
            min_balance_threshold=risk_config.get('min_balance_threshold', 10.0),
            daily_loss_limit=risk_config.get('daily_loss_limit', 0),
            max_daily_trades=risk_config.get('max_daily_trades', 0)
        )
        
        mode = self.config.mode
        self.logger.info(f"Trading mode: {mode}")
        
        if mode == 'trend_analysis':
            self.trading_mode = TrendAnalysisMode(
                config=self.config.trend_analysis_config,
                order_executor=self.order_executor,
                risk_manager=self.risk_manager,
                logger=self.logger
            )
        elif mode == 'copy_trading':
            ws_url = polymarket_config.get('ws_url', 'wss://ws-subscriptions.polymarket.com')
            self.trading_mode = CopyTradingMode(
                config=self.config.copy_trading_config,
                order_executor=self.order_executor,
                risk_manager=self.risk_manager,
                logger=self.logger,
                ws_url=ws_url
            )
        else:
            self.logger.error(f"Unknown trading mode: {mode}")
            raise ValueError(f"Unknown trading mode: {mode}")
        
        self.running = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    async def start(self):
        self.running = True
        
        self.logger.info("Configuration:")
        self.logger.info(f"  Mode: {self.config.mode}")
        self.logger.info(f"  Paper Trading: {self.config.paper_trading}")
        self.logger.info(f"  Max Bet Size: {self.risk_manager.max_bet_size} USDC")
        self.logger.info(f"  Min Balance Threshold: {self.risk_manager.min_balance_threshold} USDC")
        
        balance = self.order_executor.get_balance()
        self.logger.info(f"Initial Balance: {balance:.2f} USDC")
        
        risk_summary = self.risk_manager.get_risk_summary()
        self.logger.info(f"Risk Management: {risk_summary}")
        
        try:
            await self.trading_mode.run()
        
        except Exception as e:
            self.logger.error(f"Error in main bot loop: {e}", exc_info=True)
        
        finally:
            self.logger.info("Bot stopped")
            
            final_balance = self.order_executor.get_balance()
            self.logger.info(f"Final Balance: {final_balance:.2f} USDC")
            
            if self.config.paper_trading:
                pnl = self.order_executor.get_pnl()
                self.logger.info(f"Total PnL: {pnl:.2f} USDC")
                
                summary = self.order_executor.get_account_summary()
                self.logger.info(f"Account Summary: {summary}")
            
            self.logger.info("=" * 60)
            self.logger.info("Polymarket Trading Bot Stopped")
            self.logger.info("=" * 60)
    
    def stop(self):
        if self.running:
            self.logger.info("Stopping bot...")
            self.running = False
            
            if hasattr(self.trading_mode, 'stop'):
                self.trading_mode.stop()


async def main():
    try:
        bot = PolymarketBot()
        await bot.start()
    
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
