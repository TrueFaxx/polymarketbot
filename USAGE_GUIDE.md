# Polymarket Trading Bot - Usage Guide

## Getting Started

### Step 1: Installation

```bash
# Clone or download the repository
cd polymarket-bot

# Run the start script (creates venv and installs dependencies)
./start.sh
```

### Step 2: Configuration

#### For Paper Trading (Recommended First)

1. Open `config.yaml`
2. Ensure these settings:
```yaml
mode: trend_analysis  # or copy_trading
paper_trading: true
```

3. That's it! You can run the bot without any API credentials.

#### For Live Trading

1. Create `.env` file:
```bash
cp .env.example .env
```

2. Add your Polymarket credentials to `.env`:
```env
POLYMARKET_PRIVATE_KEY=your_private_key_here
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_API_SECRET=your_api_secret_here
POLYMARKET_PASSPHRASE=your_passphrase_here
```

3. Update `config.yaml`:
```yaml
paper_trading: false
```

### Step 3: Run the Bot

```bash
python main.py
```

Or use the start script:
```bash
./start.sh
```

## Trading Modes

### Mode 1: Bitcoin Trend Analysis

This mode analyzes Bitcoin price trends every 15 minutes and generates trading signals.

**How it works:**
1. Fetches Bitcoin price data from Binance/Coinbase
2. Calculates technical indicators (EMA, RSI, MACD)
3. Generates BUY/SELL signals based on indicator crossovers
4. Executes trades on Polymarket's Bitcoin 15min up/down market

**Configuration:**
```yaml
mode: trend_analysis

trend_analysis:
  interval: 15              # Check every 15 minutes
  exchange: binance         # or 'coinbase'
  symbol: BTC/USDT
  market_id: ""            # Set to actual Polymarket market ID
  
  indicators:
    ema_short: 9           # Fast EMA period
    ema_long: 21           # Slow EMA period
    rsi_period: 14         # RSI period
  
  signals:
    rsi_overbought: 70     # RSI upper threshold
    rsi_oversold: 30       # RSI lower threshold
```

**Trading Signals:**
- **BUY**: When EMA(9) crosses above EMA(21) AND RSI < 70
- **SELL**: When EMA(9) crosses below EMA(21) AND RSI > 30
- **HOLD**: No clear signal

**Example Output:**
```
2026-01-07 10:15:00 - INFO - SIGNAL - TREND_ANALYSIS - BUY - Reason: Bullish EMA crossover (EMA9 > EMA21) and RSI 45.32 < 70
2026-01-07 10:15:01 - INFO - PAPER TRADE - TREND_ANALYSIS - BUY 200 @ 0.5 - Market: Bitcoin 15min Up/Down - Result: success
```

### Mode 2: Copy Trading

This mode monitors a target wallet and replicates their trades in real-time.

**How it works:**
1. Connects to Polymarket WebSocket
2. Subscribes to target user's trade events
3. Detects trades within seconds
4. Replicates the trade with optional position scaling

**Configuration:**
```yaml
mode: copy_trading

copy_trading:
  target_wallet: "0x1234..."    # Wallet address to copy
  position_scale: 1.0           # 1.0 = same size, 0.5 = half
  max_delay: 5                  # Max seconds to replicate
```

**Example Output:**
```
2026-01-07 10:20:15 - INFO - Detected trade from target user: BUY 100 @ 0.65 on Presidential Election 2024
2026-01-07 10:20:16 - INFO - Replicating trade: BUY 100 @ 0.65
2026-01-07 10:20:17 - INFO - PAPER TRADE - COPY_TRADING - BUY 100 @ 0.65 - Market: Presidential Election 2024 - Result: success
```

## Paper Trading

Paper trading simulates trades without using real money.

**Features:**
- Tracks virtual balance (default: $10,000 USDC)
- Records all trades in `paper_trades.json`
- Calculates profit/loss
- Tracks open positions
- Identical behavior to live trading

**To enable:**
```yaml
paper_trading: true
paper_trading_settings:
  initial_balance: 10000.0
  track_pnl: true
```

**View paper trading results:**
```bash
cat paper_trades.json
```

## Risk Management

### Configuration Options

```yaml
risk_management:
  max_bet_size: 100.0           # Max USDC per trade
  min_balance_threshold: 10.0   # Stop if balance below
  daily_loss_limit: 500.0       # Stop if daily loss exceeds
  max_daily_trades: 20          # Max trades per day
```

### How Risk Management Works

1. **Pre-Trade Checks**: Before every trade, the bot checks:
   - Is trade size within max_bet_size?
   - Is balance sufficient?
   - Will balance stay above min_balance_threshold?
   - Have we hit daily trade limit?
   - Have we hit daily loss limit?

2. **Trade Blocking**: If any check fails, the trade is blocked and logged.

3. **Emergency Stop**: The bot stops trading if balance falls below threshold.

### Example Risk Check:
```
2026-01-07 10:25:00 - WARNING - Trade blocked by risk manager: Trade cost (150.00) exceeds max bet size (100.00)
```

## Monitoring

### Real-Time Console Output

The bot prints real-time information:
```
============================================================
Polymarket Trading Bot Starting
============================================================

2026-01-07 10:00:00 - INFO - Trading mode: trend_analysis
2026-01-07 10:00:00 - INFO - Paper Trading: True
2026-01-07 10:00:00 - INFO - Initial Balance: 10000.00 USDC
2026-01-07 10:00:01 - INFO - Starting Bitcoin Trend Analysis mode
```

### Log Files

**Bot Log** (`logs/bot_20260107.log`):
```
2026-01-07 10:15:00 - PolymarketBot - INFO - Fetching Bitcoin price data...
2026-01-07 10:15:01 - PolymarketBot - INFO - Calculating technical indicators...
2026-01-07 10:15:02 - PolymarketBot - INFO - SIGNAL - TREND_ANALYSIS - BUY
```

**Trade Log** (`logs/trades_20260107.jsonl`):
```json
{"timestamp": "2026-01-07T10:15:02", "mode": "trend_analysis", "market": "btc_15min", "side": "buy", "size": 200, "price": 0.5, "result": "success", "paper_trade": true}
```

### Viewing Logs

```bash
# Watch live logs
tail -f logs/bot_$(date +%Y%m%d).log

# View trade history
cat logs/trades_$(date +%Y%m%d).jsonl | jq
```

## Advanced Configuration

### Custom Technical Indicators

Modify indicator parameters in `config.yaml`:

```yaml
trend_analysis:
  indicators:
    ema_short: 5      # Faster signals (more trades)
    ema_long: 15      # Faster signals
    rsi_period: 10    # More sensitive RSI
```

**Trade-offs:**
- Shorter periods = More signals, more false positives
- Longer periods = Fewer signals, more reliable

### Position Sizing for Copy Trading

```yaml
copy_trading:
  position_scale: 0.5  # Trade half the size of target user
```

**Use cases:**
- `position_scale: 2.0` - Trade double the size (higher risk)
- `position_scale: 0.5` - Trade half the size (lower risk)
- `position_scale: 1.0` - Trade same size

### Multiple Exchange Support

```yaml
trend_analysis:
  exchange: coinbase  # Switch to Coinbase
  symbol: BTC/USD     # Different symbol
```

Supported exchanges: `binance`, `coinbase`, `kraken`, etc. (via CCXT)

## Stopping the Bot

### Graceful Shutdown

Press `Ctrl+C` to stop the bot gracefully:
```
^C
2026-01-07 10:30:00 - INFO - Received signal 2, shutting down gracefully...
2026-01-07 10:30:01 - INFO - Stopping bot...
2026-01-07 10:30:02 - INFO - Final Balance: 10150.00 USDC
2026-01-07 10:30:02 - INFO - Total PnL: 150.00 USDC
```

The bot will:
1. Stop accepting new signals
2. Close WebSocket connections
3. Save paper trading state
4. Log final balance and summary

## Troubleshooting

### Common Issues

**1. "No module named 'py_clob_client'"**
```bash
pip install -r requirements.txt
```

**2. "Failed to fetch price data"**
- Check internet connection
- Try different exchange: `exchange: coinbase`
- Check if exchange requires API keys

**3. "Client not initialized" (Paper Trading)**
- This is normal for paper trading
- The bot will still work correctly

**4. No trades executing**
- Check if signals are being generated (look for "SIGNAL" in logs)
- Verify risk management settings aren't too restrictive
- For trend analysis: ensure market_id is set
- For copy trading: ensure target_wallet is correct

**5. WebSocket disconnecting**
- The bot will automatically reconnect
- Check Polymarket API status
- Verify internet connection stability

### Debug Mode

Enable debug logging in `config.yaml`:
```yaml
logging:
  level: DEBUG
```

This will show detailed information about:
- Price data fetching
- Indicator calculations
- Signal generation logic
- WebSocket messages
- Risk checks

## Best Practices

### 1. Start with Paper Trading
Always test your configuration with paper trading first:
```yaml
paper_trading: true
```

### 2. Use Conservative Risk Settings
Start with small limits:
```yaml
risk_management:
  max_bet_size: 10.0      # Small size
  min_balance_threshold: 50.0
  daily_loss_limit: 50.0
```

### 3. Monitor Regularly
Check the bot at least once per hour initially.

### 4. Keep Logs
Logs are stored in `logs/` directory. Review them regularly.

### 5. Test Configuration Changes
Always test changes in paper trading mode first.

### 6. Backup Configuration
Keep backups of your `config.yaml` and `.env` files.

### 7. Understand the Strategy
Make sure you understand how the trading signals work before going live.

## Performance Tracking

### View Paper Trading Summary

```python
import json

with open('paper_trades.json', 'r') as f:
    data = json.load(f)
    print(f"Balance: ${data['balance']:.2f}")
    print(f"Total PnL: ${data['total_pnl']:.2f}")
    print(f"Total Trades: {len(data['trades'])}")
```

### Analyze Trade History

```bash
# Count trades by result
cat logs/trades_*.jsonl | jq -r '.result' | sort | uniq -c

# Calculate average trade size
cat logs/trades_*.jsonl | jq -r '.size' | awk '{sum+=$1; count++} END {print sum/count}'

# View trades by mode
cat logs/trades_*.jsonl | jq 'select(.mode=="trend_analysis")'
```

## Getting Help

1. Check this guide
2. Review the README.md
3. Check log files for errors
4. Enable DEBUG logging
5. Review configuration settings

## Next Steps

1. ✅ Run bot in paper trading mode
2. ✅ Monitor for 24 hours
3. ✅ Review trade logs and performance
4. ✅ Adjust configuration if needed
5. ✅ Test with small live amounts
6. ✅ Gradually increase position sizes

Remember: Always start small and test thoroughly!

