# src/modes/copy_trading.py

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Set, Optional

try:
    import aiohttp
except ImportError as e:
    aiohttp = None

from ..polymarket.order_executor import OrderExecutor
from ..risk.risk_manager import RiskManager
from ..utils.logger import TradingLogger


class CopyTradingMode:
    """
    Copy trades from a target wallet with minimal latency.

    NOTE:
    - The Polymarket CLOB websocket 'user' stream is authenticated (meant for YOUR account),
      so it won't reliably stream trades for arbitrary wallets.
    - To follow any wallet, we poll Polymarket Data API /activity with a timestamp cursor.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        order_executor: OrderExecutor,
        risk_manager: RiskManager,
        logger: TradingLogger,
        ws_url: Optional[str] = None,  # kept for backward compatibility (ignored)
        data_api_url: str = "https://data-api.polymarket.com/activity",
    ):
        self.config = config
        self.order_executor = order_executor
        self.risk_manager = risk_manager
        self.logger = logger

        # Back-compat: main.py still passes this sometimes
        self.ws_url = ws_url

        # Core config
        self.target_wallet = (config.get("target_wallet") or "").strip()
        self.position_scale = float(config.get("position_scale", 1.0))
        self.position_size_pct = float(config.get("position_size_pct", 0.0))
        self.max_delay = float(config.get("max_delay", 5))  # seconds

        # Latency knobs
        # 0.25–0.50s is a good range for speed without being dumb.
        self.poll_interval = float(config.get("poll_interval", 0.35))
        self.batch_limit = int(config.get("poll_batch_limit", 200))
        self.queue_max = int(config.get("queue_max", 2000))

        self.data_api_url = data_api_url

        # Runtime state
        self.running = False
        self.processed_trades: Set[str] = set()
        self._last_ts: Optional[int] = None  # Data API timestamp cursor (int)
        self._q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=self.queue_max)

        self._poll_task: Optional[asyncio.Task] = None
        self._consume_task: Optional[asyncio.Task] = None

    # --------------------
    # Helpers
    # --------------------

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _ts_to_ms(ts: Any) -> int:
        """
        Data API timestamps can show up as seconds or milliseconds depending on endpoint/version.
        Handle both.
        """
        try:
            ts_i = int(ts)
        except Exception:
            return CopyTradingMode._now_ms()

        # < 10^10 => seconds-ish
        if ts_i < 10_000_000_000:
            return ts_i * 1000
        return ts_i

    def _generate_trade_id(self, trade_data: Dict[str, Any]) -> str:
        # Best dedupe key
        tx = trade_data.get("tx_hash") or trade_data.get("transactionHash")
        if tx:
            return str(tx)

        wallet = trade_data.get("wallet", "")
        market = trade_data.get("market", "")
        timestamp = trade_data.get("timestamp", "")
        side = trade_data.get("side", "")
        return f"{wallet}_{market}_{timestamp}_{side}"

    def _shrink_dedupe_set(self) -> None:
        # Avoid unbounded growth
        if len(self.processed_trades) > 3000:
            self.processed_trades = set(list(self.processed_trades)[-1500:])

    # --------------------
    # Trade handling
    # --------------------

    async def _handle_user_trade(self, trade_data: Dict[str, Any]):
        try:
            trade_id = self._generate_trade_id(trade_data)
            if trade_id in self.processed_trades:
                return

            self.processed_trades.add(trade_id)
            self._shrink_dedupe_set()

            wallet = (trade_data.get("wallet") or "").strip()
            if wallet.lower() != self.target_wallet.lower():
                return

            market_id = trade_data.get("market", "")
            token_id = trade_data.get("token_id", "")
            side = str(trade_data.get("side", "buy")).lower()
            size = float(trade_data.get("size", 0) or 0)
            price = float(trade_data.get("price", 0.5) or 0.5)
            market_name = trade_data.get("market_name", market_id) or market_id

            # scale
            scaled_size = size * self.position_scale
            balance = self.order_executor.get_balance()
            pct_size = None
            if self.position_size_pct > 0 and side == "buy":
                pct_size = (balance * self.position_size_pct) / price if price > 0 else 0
                scaled_size = pct_size

            self.logger.info(
                f"Detected target trade: {side.upper()} {size} @ {price} on {market_name} | copying {scaled_size}"
            )

            # Risk check
            risk_check = self.risk_manager.check_pre_trade(scaled_size, price, balance)
            if not risk_check.get("allowed", False):
                self.logger.warning(f"Copy trade blocked by risk manager: {risk_check.get('reason', 'unknown')}")
                return

            # Don’t block event loop while placing order
            result = await asyncio.to_thread(
                self.order_executor.execute_limit_order,
                token_id=token_id,
                side=side,
                size=scaled_size,
                price=price,
                market_id=market_id,
                market_name=market_name,
            )

            trade_log = {
                "timestamp": datetime.now().isoformat(),
                "mode": "copy_trading",
                "market": market_id,
                "market_name": market_name,
                "side": side,
                "size": scaled_size,
                "price": result.get("price", price),
                "result": "success" if result.get("success") else "failed",
                "paper_trade": result.get("paper_trade", False),
                "reason": f"Copied from {wallet[:8]}...",
                "original_size": size,
                "scale_factor": self.position_scale,
                "position_size_pct": self.position_size_pct,
                "tx_hash": trade_data.get("tx_hash"),
            }

            if not result.get("success"):
                trade_log["error"] = result.get("error", "Unknown error")

            self.logger.log_trade(trade_log)

            if result.get("success"):
                self.risk_manager.record_trade(trade_log)

        except Exception as e:
            self.logger.error(f"Error handling user trade: {e}", exc_info=True)

    # --------------------
    # Data API Polling
    # --------------------

    async def _bootstrap_cursor(self, session: "aiohttp.ClientSession") -> None:
        """
        Start at the newest event so we don't replay history on startup.
        """
        params = {
            "user": self.target_wallet,
            "type": "TRADE",
            "limit": 1,
            "offset": 0,
            "sortBy": "TIMESTAMP",
            "sortDirection": "DESC",
        }
        async with session.get(self.data_api_url, params=params) as r:
            r.raise_for_status()
            data = await r.json()

        if data:
            self._last_ts = int(data[0].get("timestamp", 0))
        else:
            self._last_ts = 0

        self.logger.info(f"Bootstrapped cursor at timestamp={self._last_ts}")

    async def _poll_loop(self) -> None:
        if aiohttp is None:
            raise RuntimeError("aiohttp is not installed. Run: pip install aiohttp")

        connector = aiohttp.TCPConnector(
            limit=20,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
        )
        timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=10)

        backoff = 0.2

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            await self._bootstrap_cursor(session)

            while self.running:
                try:
                    start_ts = (self._last_ts + 1) if self._last_ts is not None else 0

                    params = {
                        "user": self.target_wallet,
                        "type": "TRADE",
                        "limit": self.batch_limit,
                        "offset": 0,
                        "start": start_ts,
                        "sortBy": "TIMESTAMP",
                        "sortDirection": "ASC",
                    }

                    async with session.get(self.data_api_url, params=params) as r:
                        r.raise_for_status()
                        items = await r.json()

                    if items:
                        # advance cursor immediately
                        for it in items:
                            ts = int(it.get("timestamp", 0))
                            if self._last_ts is None or ts > self._last_ts:
                                self._last_ts = ts

                        # enqueue events
                        for it in items:
                            if self._q.full():
                                # drop oldest to keep latency low
                                _ = self._q.get_nowait()
                                self._q.task_done()
                            await self._q.put(it)

                    backoff = 0.2
                    await asyncio.sleep(self.poll_interval)

                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self.logger.warning(f"Poll error: {e} (backing off)")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 5.0)

    async def _consume_loop(self) -> None:
        while self.running:
            try:
                it = await self._q.get()

                tx = it.get("transactionHash")
                if tx and tx in self.processed_trades:
                    self._q.task_done()
                    continue

                # latency gate: skip trades that are too old
                trade_ms = self._ts_to_ms(it.get("timestamp"))
                if self.max_delay and (self._now_ms() - trade_ms) > int(self.max_delay * 1000):
                    self._q.task_done()
                    continue

                # normalize event -> trade_data expected by handler
                trade_data = {
                    "tx_hash": tx,
                    "wallet": it.get("proxyWallet", ""),
                    "market": it.get("conditionId", ""),
                    "token_id": it.get("asset", ""),
                    "side": str(it.get("side", "BUY")).lower(),  # BUY/SELL -> buy/sell
                    "size": float(it.get("size", 0) or 0),
                    "price": float(it.get("price", 0.5) or 0.5),
                    "timestamp": it.get("timestamp"),
                    "market_name": it.get("title") or it.get("conditionId", ""),
                }

                await self._handle_user_trade(trade_data)
                self._q.task_done()

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f"Consume error: {e}", exc_info=True)

    # --------------------
    # Public API
    # --------------------

    async def run(self):
        self.running = True
        self.logger.info("Starting Copy Trading mode (low-latency Data API)")
        self.logger.info(f"Target wallet: {self.target_wallet}")
        self.logger.info(f"Position scale: {self.position_scale}x")
        self.logger.info(f"Poll interval: {self.poll_interval}s")

        if not self.target_wallet:
            self.logger.error("No target wallet specified in configuration")
            self.running = False
            return

        balance = self.order_executor.get_balance()
        self.logger.log_balance({"balance": balance, "paper_trade": self.order_executor.paper_trading})

        self._poll_task = asyncio.create_task(self._poll_loop(), name="copytrade_poller")
        self._consume_task = asyncio.create_task(self._consume_loop(), name="copytrade_consumer")

        try:
            done, _ = await asyncio.wait(
                {self._poll_task, self._consume_task},
                return_when=asyncio.FIRST_EXCEPTION,
            )

            # bubble exceptions
            for t in done:
                exc = t.exception()
                if exc:
                    raise exc

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in copy trading mode: {e}", exc_info=True)
        finally:
            self.running = False

            for t in (self._poll_task, self._consume_task):
                if t and not t.done():
                    t.cancel()

            await asyncio.gather(
                *(t for t in (self._poll_task, self._consume_task) if t),
                return_exceptions=True,
            )

            self.logger.info("Copy trading mode stopped")

    def stop(self):
        self.running = False
        self.logger.info("Stopping copy trading mode...")
