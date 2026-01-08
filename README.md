# Polymarket Auto Trading Bot

An automated trading bot for Polymarket with two modes:
1. **Bitcoin Trend Analysis**: Analyzes 15-minute Bitcoin price trends using technical indicators and trades accordingly
2. **Copy Trading**: Replicates trades from a specified user in real-time via WebSocket

## Features

- 🎯 Two trading modes with easy configuration
- 📊 Paper trading mode for risk-free testing
- 📈 Technical analysis with EMA, RSI, and MACD indicators
- ⚡ Real-time WebSocket integration for copy trading
- 🛡️ Risk management safeguards (max bet size, balance thresholds, daily limits)
- 📝 Comprehensive logging and trade tracking
- 🔄 Automatic reconnection for WebSocket connections
- 💰 Position sizing and scaling options

## Quick Start

### Option 1: Using the start script (recommended)
```bash
./start.sh
```

### Option 2: Manual setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your API keys

# Configure bot settings
nano config.yaml  # or use your preferred editor

# Run the bot
python main.py
```

## Configuration

### 1. Environment Variables (.env)

Create a `.env` file with your credentials:

```env
# Polymarket Credentials (required for live trading)
POLYMARKET_PRIVATE_KEY=your_ethereum_private_key
POLYMARKET_API_KEY=your_api_key
POLYMARKET_API_SECRET=your_api_secret
POLYMARKET_PASSPHRASE=your_passphrase

# Exchange API Keys (optional, for price data)
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
```

**Note**: For paper trading mode, you don't need Polymarket credentials.

### 2. Bot Configuration (config.yaml)

#### Trading Mode Selection
```yaml
mode: trend_analysis  # or 'copy_trading'
```

#### Paper Trading (Recommended for Testing)
```yaml
paper_trading: true
paper_trading_settings:
  initial_balance: 10000.0  # Starting balance in USDC
  track_pnl: true
```

#### Mode 1: Bitcoin Trend Analysis
```yaml
trend_analysis:
  interval: 15  # Analysis interval in minutes
  
  indicators:
    ema_short: 9
    ema_long: 21
    rsi_period: 14
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
  
  signals:
    rsi_overbought: 70
    rsi_oversold: 30
  
  market_id: ""  # Polymarket Bitcoin 15min market ID
  exchange: binance  # or 'coinbase'
  symbol: BTC/USDT
```

**Trading Strategy**:
- **BUY Signal**: EMA(9) crosses above EMA(21) AND RSI < 70
- **SELL Signal**: EMA(9) crosses below EMA(21) AND RSI > 30

#### Mode 2: Copy Trading
```yaml
copy_trading:
  target_wallet: "0x..."  # Wallet address to copy
  position_scale: 1.0     # 1.0 = same size, 0.5 = half size
  max_delay: 5            # Max seconds to replicate trade
```

#### Risk Management
```yaml
risk_management:
  max_bet_size: 100.0           # Maximum per trade (USDC)
  min_balance_threshold: 10.0   # Stop if balance below this
  daily_loss_limit: 0           # 0 = disabled
  max_daily_trades: 0           # 0 = unlimited
```

## Usage Examples

### Example 1: Paper Trading Bitcoin Trends

1. Edit `config.yaml`:
```yaml
mode: trend_analysis
paper_trading: true
```

2. Run the bot:
```bash
python main.py
```

3. Monitor logs in `logs/` directory

### Example 2: Copy Trading (Paper Mode)

1. Edit `config.yaml`:
```yaml
mode: copy_trading
paper_trading: true
copy_trading:
  target_wallet: "0x1234..."  # Replace with actual wallet
```

2. Run the bot:
```bash
python main.py
```

### Example 3: Live Trading (Real Money)

⚠️ **WARNING**: This uses real money!

1. Configure `.env` with your Polymarket credentials
2. Edit `config.yaml`:
```yaml
mode: trend_analysis
paper_trading: false
risk_management:
  max_bet_size: 10.0  # Start small!
```

3. Run the bot:
```bash
python main.py
```

## Project Structure

```
polymarket-bot/
├── main.py                          # Main entry point
├── start.sh                         # Quick start script
├── config.yaml                      # Configuration file
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create this)
├── src/
│   ├── config.py                   # Configuration loader
│   ├── polymarket/
│   │   ├── api_client.py          # Polymarket API wrapper
│   │   ├── websocket_client.py    # WebSocket client
│   │   ├── order_executor.py      # Order execution
│   │   └── paper_trading.py       # Paper trading simulator
│   ├── modes/
│   │   ├── trend_analysis.py      # Bitcoin trend analysis mode
│   │   └── copy_trading.py        # Copy trading mode
│   ├── risk/
│   │   └── risk_manager.py        # Risk management
│   └── utils/
│       ├── logger.py              # Logging utilities
│       └── data_aggregator.py     # Price data aggregation
├── logs/                           # Log files (auto-created)
│   ├── bot_YYYYMMDD.log          # Daily bot logs
│   └── trades_YYYYMMDD.jsonl     # Trade logs (JSON Lines)
└── paper_trades.json              # Paper trading state (auto-created)
```

## Monitoring

### Logs

The bot creates two types of logs:

1. **Bot Logs** (`logs/bot_YYYYMMDD.log`): General bot activity
2. **Trade Logs** (`logs/trades_YYYYMMDD.jsonl`): Detailed trade records in JSON format

### Console Output

The bot outputs real-time information to the console:
- Balance updates
- Trading signals
- Trade executions
- Risk management decisions
- Errors and warnings

## Risk Management

The bot includes several safety features:

1. **Max Bet Size**: Limits the maximum amount per trade
2. **Balance Threshold**: Stops trading if balance falls below threshold
3. **Daily Loss Limit**: Stops trading if daily losses exceed limit
4. **Daily Trade Limit**: Limits number of trades per day
5. **Pre-trade Validation**: Checks all parameters before execution
6. **Emergency Stop**: Can be triggered manually if needed

## Troubleshooting

### "Client not initialized" error
- Check your `.env` file has correct credentials
- For paper trading, this warning is normal and can be ignored

### No trades being executed
- Check if you're in paper trading mode
- Verify your risk management settings aren't too restrictive
- Check logs for signal generation
- Ensure market_id is set correctly for trend analysis mode

### WebSocket connection issues
- Check your internet connection
- The bot will automatically reconnect
- Check Polymarket WebSocket status

### Price data not updating
- Verify exchange API is accessible (Binance/Coinbase)
- Check if you need API keys for the exchange
- Try switching to a different exchange in config

## Safety Guidelines

⚠️ **IMPORTANT**: Always follow these safety guidelines:

1. **Start with Paper Trading**: Test your strategy thoroughly before using real money
2. **Start Small**: When going live, start with very small position sizes
3. **Monitor Regularly**: Check the bot's performance frequently
4. **Set Conservative Limits**: Use strict risk management settings
5. **Understand the Strategy**: Make sure you understand how the trading signals work
6. **Test Configuration Changes**: Use paper trading to test any configuration changes
7. **Keep Credentials Safe**: Never share your `.env` file or private keys
8. **Regular Backups**: Back up your configuration and logs regularly

## Technical Details

### Dependencies

- `py-clob-client`: Official Polymarket Python client
- `websockets`: WebSocket communication
- `ccxt`: Unified cryptocurrency exchange API
- `pandas`: Data manipulation
- `ta`: Technical analysis indicators
- `pyyaml`: Configuration file handling
- `python-dotenv`: Environment variable management

### Technical Indicators

**EMA (Exponential Moving Average)**:
- Short period (default: 9) and long period (default: 21)
- Crossovers indicate trend changes

**RSI (Relative Strength Index)**:
- Measures momentum (0-100)
- Above 70: overbought, Below 30: oversold

**MACD (Moving Average Convergence Divergence)**:
- Trend-following momentum indicator
- Shows relationship between two EMAs

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Disclaimer

This bot is for educational purposes only. Trading cryptocurrencies and prediction markets involves substantial risk of loss. The authors are not responsible for any financial losses incurred while using this software. Always do your own research and never invest more than you can afford to lose.

## License

MIT License - See LICENSE file for details

