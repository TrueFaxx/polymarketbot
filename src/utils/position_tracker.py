from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PositionSnapshot:
    market_id: str
    market_name: str
    size: float
    avg_price: float
    entry_time: str
    last_update: str


@dataclass
class ClosedPosition:
    market_id: str
    market_name: str
    size: float
    avg_entry_price: float
    exit_price: float
    realized_pnl: float
    entry_time: str
    exit_time: str


class PositionTracker:
    def __init__(self, data_file: str = "copy_positions.json", max_closed: int = 200):
        self.data_file = data_file
        self.max_closed = max_closed
        self.positions: Dict[str, PositionSnapshot] = {}
        self.closed_positions: List[ClosedPosition] = []
        self.realized_pnl_total = 0.0
        self._load_data()

    def _load_data(self) -> None:
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, "r") as handle:
                data = json.load(handle)
        except Exception:
            return

        self.realized_pnl_total = float(data.get("realized_pnl_total", 0.0))
        self.positions = {}
        for market_id, payload in data.get("positions", {}).items():
            try:
                self.positions[market_id] = PositionSnapshot(**payload)
            except TypeError:
                continue

        self.closed_positions = []
        for payload in data.get("closed_positions", []):
            try:
                self.closed_positions.append(ClosedPosition(**payload))
            except TypeError:
                continue

    def _save_data(self) -> None:
        try:
            with open(self.data_file, "w") as handle:
                json.dump(
                    {
                        "positions": {mid: asdict(pos) for mid, pos in self.positions.items()},
                        "closed_positions": [asdict(pos) for pos in self.closed_positions],
                        "realized_pnl_total": self.realized_pnl_total,
                        "last_updated": datetime.now().isoformat(),
                    },
                    handle,
                    indent=2,
                )
        except Exception:
            return

    def record_trade(
        self,
        market_id: str,
        market_name: str,
        side: str,
        size: float,
        price: float,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        ts = timestamp or datetime.now().isoformat()
        side_lower = side.lower()
        size = float(size)
        price = float(price)
        market_name = market_name or market_id

        if side_lower == "buy":
            position = self.positions.get(market_id)
            if position:
                total_size = position.size + size
                avg_price = ((position.size * position.avg_price) + (size * price)) / total_size
                position.size = total_size
                position.avg_price = avg_price
                position.last_update = ts
                status = "increased"
            else:
                position = PositionSnapshot(
                    market_id=market_id,
                    market_name=market_name,
                    size=size,
                    avg_price=price,
                    entry_time=ts,
                    last_update=ts,
                )
                self.positions[market_id] = position
                status = "opened"
            self._save_data()
            return {
                "status": status,
                "position": asdict(position),
                "realized_pnl": 0.0,
            }

        if side_lower == "sell":
            position = self.positions.get(market_id)
            if not position:
                return {
                    "status": "unmatched_sell",
                    "realized_pnl": 0.0,
                }

            sell_size = min(size, position.size)
            realized_pnl = sell_size * (price - position.avg_price)
            self.realized_pnl_total += realized_pnl

            if sell_size >= position.size:
                closed = ClosedPosition(
                    market_id=market_id,
                    market_name=position.market_name,
                    size=position.size,
                    avg_entry_price=position.avg_price,
                    exit_price=price,
                    realized_pnl=realized_pnl,
                    entry_time=position.entry_time,
                    exit_time=ts,
                )
                self.closed_positions.append(closed)
                self.closed_positions = self.closed_positions[-self.max_closed :]
                del self.positions[market_id]
                self._save_data()
                return {
                    "status": "closed",
                    "position": asdict(closed),
                    "realized_pnl": realized_pnl,
                }

            position.size -= sell_size
            position.last_update = ts
            self._save_data()
            return {
                "status": "reduced",
                "position": asdict(position),
                "realized_pnl": realized_pnl,
            }

        return {
            "status": "ignored",
            "realized_pnl": 0.0,
        }

    def snapshot(self) -> Dict[str, Any]:
        open_positions = [asdict(pos) for pos in self.positions.values()]
        closed_positions = [asdict(pos) for pos in self.closed_positions]
        return {
            "open_positions": open_positions,
            "closed_positions": closed_positions,
            "realized_pnl_total": self.realized_pnl_total,
        }
