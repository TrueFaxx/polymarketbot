from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:  # pragma: no cover - optional dependency
    Console = None
    Layout = None
    Live = None
    Panel = None
    Table = None
    Text = None


class TradingTUI:
    def __init__(
        self,
        enabled: bool = True,
        refresh_per_second: int = 4,
        max_recent_trades: int = 6,
        max_closed_positions: int = 6,
    ):
        self.enabled = enabled and Console is not None
        self.refresh_per_second = refresh_per_second
        self.max_recent_trades = max_recent_trades
        self.max_closed_positions = max_closed_positions
        self._console = Console() if self.enabled else None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._state: Dict[str, Any] = {
            "status": "starting",
            "balance": 0.0,
            "pnl": 0.0,
            "queue": "0/0",
            "last_ts": None,
            "recent_trades": [],
            "open_positions": [],
            "closed_positions": [],
            "realized_pnl": 0.0,
            "mode": "copy_trading",
        }

    def start(self) -> None:
        if not self.enabled or self._thread:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="trading_tui", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._thread:
            return
        self._stop_event.set()
        self._thread.join(timeout=2)
        self._thread = None

    def update_state(self, payload: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._state.update(payload)
            self._state["last_update"] = datetime.now().strftime("%H:%M:%S")

    def _render_header(self) -> Panel:
        status = self._state.get("status", "-")
        balance = self._state.get("balance", 0.0)
        pnl = self._state.get("pnl", 0.0)
        realized = self._state.get("realized_pnl", 0.0)
        queue = self._state.get("queue", "0/0")
        last_ts = self._state.get("last_ts")
        last_update = self._state.get("last_update", "-")
        mode = self._state.get("mode", "-")

        header = Text()
        header.append(f"Mode: {mode}\n", style="bold")
        header.append(f"Status: {status}\n")
        header.append(f"Balance: {balance:,.2f} USDC\n")
        header.append(f"PnL: {pnl:,.2f} | Realized: {realized:,.2f}\n")
        header.append(f"Queue: {queue} | Last TS: {last_ts}\n")
        header.append(f"Last update: {last_update}")
        return Panel(header, title="Bot Overview", border_style="cyan")

    def _render_open_positions(self) -> Panel:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Market", overflow="fold")
        table.add_column("Size", justify="right")
        table.add_column("Avg Price", justify="right")
        table.add_column("Entry", justify="right")

        open_positions = self._state.get("open_positions", [])
        for pos in open_positions:
            table.add_row(
                pos.get("market_name", "-") or pos.get("market_id", "-"),
                f"{pos.get('size', 0):.4f}",
                f"{pos.get('avg_price', 0):.4f}",
                pos.get("entry_time", "-")[-8:],
            )

        if not open_positions:
            table.add_row("(none)", "-", "-", "-")

        return Panel(table, title="Open Positions", border_style="green")

    def _render_closed_positions(self) -> Panel:
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Market", overflow="fold")
        table.add_column("Size", justify="right")
        table.add_column("Exit", justify="right")
        table.add_column("PnL", justify="right")

        closed_positions = list(self._state.get("closed_positions", []))[-self.max_closed_positions :]
        for pos in closed_positions:
            table.add_row(
                pos.get("market_name", "-") or pos.get("market_id", "-"),
                f"{pos.get('size', 0):.4f}",
                f"{pos.get('exit_price', 0):.4f}",
                f"{pos.get('realized_pnl', 0):+.4f}",
            )

        if not closed_positions:
            table.add_row("(none)", "-", "-", "-")

        return Panel(table, title="Closed Positions", border_style="yellow")

    def _render_recent_trades(self) -> Panel:
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Time")
        table.add_column("Side")
        table.add_column("Size", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Market", overflow="fold")
        table.add_column("Result")

        trades: List[Dict[str, Any]] = self._state.get("recent_trades", [])[-self.max_recent_trades :]
        for trade in trades:
            table.add_row(
                trade.get("timestamp", "-")[-8:],
                trade.get("side", "-").upper(),
                f"{trade.get('size', 0):.4f}",
                f"{trade.get('price', 0):.4f}",
                trade.get("market_name", "-") or trade.get("market", "-"),
                trade.get("result", "-")
            )

        if not trades:
            table.add_row("-", "-", "-", "-", "-", "-")

        return Panel(table, title="Recent Trades", border_style="blue")

    def _render_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(self._render_header(), name="header", size=9),
            Layout(name="body"),
        )
        layout["body"].split_row(
            Layout(self._render_open_positions(), name="open"),
            Layout(self._render_closed_positions(), name="closed"),
            Layout(self._render_recent_trades(), name="trades"),
        )
        return layout

    def _run(self) -> None:
        if not self.enabled:
            return
        with Live(self._render_layout(), console=self._console, refresh_per_second=self.refresh_per_second) as live:
            while not self._stop_event.is_set():
                with self._lock:
                    live.update(self._render_layout(), refresh=True)
                time.sleep(1 / max(self.refresh_per_second, 1))
