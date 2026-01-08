# Quick Reference Card

## 🚀 Quick Start

```bash
./start.sh
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `config.yaml` | Main configuration |
| `.env` | API credentials (create from .env.example) |
| `main.py` | Run the bot |
| `logs/` | Log files |
| `paper_trades.json` | Paper trading state |

## ⚙️ Configuration Quick Settings

### Enable Paper Trading (Safe)
```yaml
paper_trading: true
```

### Select Mode
```yaml
mode: trend_analysis  # or 'copy_trading'
```

### Set Risk Limits
```yaml
risk_management:
  max_bet_size: 100.0
  min_balance_threshold: 10.0
```

## 🎯 Trading Modes

### Mode 1: Trend Analysis
Analyzes Bitcoin price every 15 minutes using technical indicators.

**Signals:**
- BUY: EMA(9) crosses above EMA(21) + RSI < 70
- SELL: EMA(9) crosses below EMA(21) + RSI > 30

**Config:**
```yaml
mode: trend_analysis
trend_analysis:
  interval: 15
  exchange: binance
  symbol: BTC/USDT
```

### Mode 2: Copy Trading
Replicates trades from a target wallet in real-time.

**Config:**
```yaml
mode: copy_trading
copy_trading:
  target_wallet: "0x..."
  position_scale: 1.0
```

## 📊 Monitoring

### View Logs
```bash
# Live logs
tail -f logs/bot_$(date +%Y%m%d).log

# Trade history
cat logs/trades_$(date +%Y%m%d).jsonl | jq
```

### Check Paper Trading Balance
```bash
cat paper_trades.json | jq '.balance'
```

## 🛑 Stop the Bot

Press `Ctrl+C` for graceful shutdown.

## ⚠️ Safety Checklist

- [ ] Start with paper trading
- [ ] Test for 24 hours
- [ ] Set conservative risk limits
- [ ] Monitor regularly
- [ ] Start small if going live

## 🔧 Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run bot
python main.py

# View config
cat config.yaml

# Check balance (paper trading)
cat paper_trades.json | jq '.balance, .total_pnl'

# Count trades today
cat logs/trades_$(date +%Y%m%d).jsonl | wc -l
```

## 📈 Indicator Settings

| Indicator | Default | Purpose |
|-----------|---------|---------|
| EMA Short | 9 | Fast moving average |
| EMA Long | 21 | Slow moving average |
| RSI Period | 14 | Momentum indicator |
| RSI Overbought | 70 | Upper threshold |
| RSI Oversold | 30 | Lower threshold |

## 🛡️ Risk Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| max_bet_size | 100.0 | Max USDC per trade |
| min_balance_threshold | 10.0 | Stop if below |
| daily_loss_limit | 0 | Max daily loss (0=off) |
| max_daily_trades | 0 | Max trades/day (0=off) |

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Client not initialized" | Normal for paper trading |
| No trades executing | Check logs for signals |
| WebSocket disconnecting | Auto-reconnects, check internet |
| Price data not updating | Try different exchange |

## 📚 Documentation

- `README.md` - Main documentation
- `USAGE_GUIDE.md` - Detailed usage
- `ARCHITECTURE.md` - Technical details
- `IMPLEMENTATION_SUMMARY.md` - Feature list

## 🔑 Environment Variables

Required for live trading only:

```env
POLYMARKET_PRIVATE_KEY=your_key
POLYMARKET_API_KEY=your_key
POLYMARKET_API_SECRET=your_secret
POLYMARKET_PASSPHRASE=your_passphrase
```

## 💡 Tips

1. **Always test first** - Use paper trading
2. **Start small** - Use low max_bet_size
3. **Monitor closely** - Check logs regularly
4. **Adjust gradually** - Change one setting at a time
5. **Keep backups** - Save config.yaml changes

## 🎓 Learning Path

1. ✅ Read README.md
2. ✅ Run in paper trading mode
3. ✅ Monitor for 24 hours
4. ✅ Review USAGE_GUIDE.md
5. ✅ Adjust configuration
6. ✅ Test again
7. ⚠️ Consider live trading (optional)

## 📞 Quick Help

**Bot won't start?**
```bash
# Check Python version (need 3.9+)
python3 --version

# Reinstall dependencies
pip install -r requirements.txt
```

**Want to reset paper trading?**
```bash
rm paper_trades.json
```

**Need to change mode?**
1. Stop bot (Ctrl+C)
2. Edit config.yaml
3. Restart bot

---

**Remember:** This bot uses real money in live mode. Always test thoroughly with paper trading first!

