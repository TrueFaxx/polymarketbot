from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional


class _DashboardHandler(BaseHTTPRequestHandler):
    server_version = "PolymarketDashboard/0.1"

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send_html()
            return
        if self.path.startswith("/state"):
            self._send_state()
            return
        self.send_response(404)
        self.end_headers()

    def _send_html(self) -> None:
        html = (
            "<!doctype html>\n"
            "<html lang='en'>\n"
            "<head>\n"
            "<meta charset='utf-8' />\n"
            "<meta name='viewport' content='width=device-width, initial-scale=1' />\n"
            "<title>Polymarket Copy Trading Dashboard</title>\n"
            "<style>\n"
            "body{font-family:Arial, sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:20px;}\n"
            ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;}\n"
            ".card{background:#1e293b;padding:16px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.2);}\n"
            ".title{font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;}\n"
            ".value{font-size:24px;margin-top:6px;}\n"
            "table{width:100%;border-collapse:collapse;margin-top:12px;}\n"
            "th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #334155;font-size:13px;}\n"
            "th{color:#94a3b8;font-weight:600;}\n"
            ".status{font-weight:600;}\n"
            ".positive{color:#4ade80;}\n"
            ".negative{color:#f87171;}\n"
            "</style>\n"
            "</head>\n"
            "<body>\n"
            "<h1>Polymarket Copy Trading Dashboard</h1>\n"
            "<div class='grid'>\n"
            "<div class='card'><div class='title'>Status</div><div class='value status' id='status'>-</div></div>\n"
            "<div class='card'><div class='title'>Balance</div><div class='value' id='balance'>-</div></div>\n"
            "<div class='card'><div class='title'>PnL</div><div class='value' id='pnl'>-</div></div>\n"
            "<div class='card'><div class='title'>Queue</div><div class='value' id='queue'>-</div></div>\n"
            "</div>\n"
            "<div class='grid' style='margin-top:16px;'>\n"
            "<div class='card'>\n"
            "<div class='title'>Open Positions</div>\n"
            "<table><thead><tr><th>Market</th><th>Size</th><th>Avg Price</th></tr></thead><tbody id='open_positions'></tbody></table>\n"
            "</div>\n"
            "<div class='card'>\n"
            "<div class='title'>Closed Positions</div>\n"
            "<table><thead><tr><th>Market</th><th>Size</th><th>PnL</th></tr></thead><tbody id='closed_positions'></tbody></table>\n"
            "</div>\n"
            "<div class='card'>\n"
            "<div class='title'>Recent Trades</div>\n"
            "<table><thead><tr><th>Time</th><th>Side</th><th>Size</th><th>Price</th></tr></thead><tbody id='recent_trades'></tbody></table>\n"
            "</div>\n"
            "</div>\n"
            "<script>\n"
            "const fmt = (n) => (n === undefined || n === null) ? '-' : Number(n).toFixed(4);\n"
            "async function refresh(){\n"
            "  const res = await fetch('/state');\n"
            "  const data = await res.json();\n"
            "  document.getElementById('status').textContent = data.status || '-';\n"
            "  document.getElementById('balance').textContent = data.balance ? Number(data.balance).toFixed(2)+' USDC' : '-';\n"
            "  const pnl = data.pnl ?? 0;\n"
            "  const pnlEl = document.getElementById('pnl');\n"
            "  pnlEl.textContent = Number(pnl).toFixed(2);\n"
            "  pnlEl.className = Number(pnl) >= 0 ? 'positive' : 'negative';\n"
            "  document.getElementById('queue').textContent = data.queue || '-';\n"
            "  const openBody = document.getElementById('open_positions');\n"
            "  openBody.innerHTML = '';\n"
            "  (data.open_positions || []).forEach(pos => {\n"
            "    const row = document.createElement('tr');\n"
            "    row.innerHTML = `<td>${pos.market_name || pos.market_id}</td><td>${fmt(pos.size)}</td><td>${fmt(pos.avg_price)}</td>`;\n"
            "    openBody.appendChild(row);\n"
            "  });\n"
            "  if (!openBody.children.length){openBody.innerHTML = '<tr><td colspan=3>-</td></tr>';}\n"
            "  const closedBody = document.getElementById('closed_positions');\n"
            "  closedBody.innerHTML = '';\n"
            "  (data.closed_positions || []).slice(-6).forEach(pos => {\n"
            "    const row = document.createElement('tr');\n"
            "    const pnlVal = Number(pos.realized_pnl || 0);\n"
            "    row.innerHTML = `<td>${pos.market_name || pos.market_id}</td><td>${fmt(pos.size)}</td><td class='${pnlVal>=0?'positive':'negative'}'>${fmt(pos.realized_pnl)}</td>`;\n"
            "    closedBody.appendChild(row);\n"
            "  });\n"
            "  if (!closedBody.children.length){closedBody.innerHTML = '<tr><td colspan=3>-</td></tr>';}\n"
            "  const tradesBody = document.getElementById('recent_trades');\n"
            "  tradesBody.innerHTML = '';\n"
            "  (data.recent_trades || []).slice(-6).forEach(tr => {\n"
            "    const row = document.createElement('tr');\n"
            "    row.innerHTML = `<td>${(tr.timestamp||'').slice(-8)}</td><td>${(tr.side||'').toUpperCase()}</td><td>${fmt(tr.size)}</td><td>${fmt(tr.price)}</td>`;\n"
            "    tradesBody.appendChild(row);\n"
            "  });\n"
            "  if (!tradesBody.children.length){tradesBody.innerHTML = '<tr><td colspan=4>-</td></tr>';}\n"
            "}\n"
            "refresh();\n"
            "setInterval(refresh, 2000);\n"
            "</script>\n"
            "</body>\n"
            "</html>\n"
        )
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_state(self) -> None:
        state = getattr(self.server, "dashboard_state", {})  # type: ignore[attr-defined]
        payload = json.dumps(state).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


class DashboardServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread:
            return
        self._server = ThreadingHTTPServer((self.host, self.port), _DashboardHandler)
        self._server.dashboard_state = {}
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._server:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def update_state(self, payload: Dict[str, Any]) -> None:
        if self._server:
            self._server.dashboard_state = payload
