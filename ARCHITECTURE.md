# Polymarket Trading Bot - Architecture

## Overview

This document describes the architecture and design decisions of the Polymarket Trading Bot.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Main Controller                       │
│                         (main.py)                           │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──► Config Manager (src/config.py)
             │
             ├──► Logger (src/utils/logger.py)
             │
             ├──► Risk Manager (src/risk/risk_manager.py)
             │
             ├──► Order Executor (src/polymarket/order_executor.py)
             │    │
             │    ├──► API Client (src/polymarket/api_client.py)
             │    └──► Paper Trading (src/polymarket/paper_trading.py)
             │
             └──► Trading Modes
                  │
                  ├──► Trend Analysis (src/modes/trend_analysis.py)
                  │    └──► Data Aggregator (src/utils/data_aggregator.py)
                  │
                  └──► Copy Trading (src/modes/copy_trading.py)
                       └──► WebSocket Client (src/polymarket/websocket_client.py)
```

## Core Components

### 1. Main Controller (`main.py`)

**Responsibilities:**
- Initialize all components
- Load configuration
- Start selected trading mode
- Handle graceful shutdown
- Log final summary

**Key Features:**
- Signal handling (SIGINT, SIGTERM)
- Error handling and recovery
- Component lifecycle management

### 2. Configuration Manager (`src/config.py`)

**Responsibilities:**
- Load YAML configuration
- Load environment variables
- Provide typed access to config values

**Design Pattern:** Singleton-like configuration object

### 3. Logger (`src/utils/logger.py`)

**Responsibilities:**
- Structured logging
- Trade logging (JSONL format)
- Daily log rotation
- Console and file output

**Log Types:**
- Bot logs: General activity
- Trade logs: Detailed trade records
- Signal logs: Trading signals generated
- Balance logs: Balance updates

### 4. API Client (`src/polymarket/api_client.py`)

**Responsibilities:**
- Wrapper for py-clob-client
- Market data fetching
- Order placement
- Balance queries
- Position tracking

**Key Features:**
- Error handling
- Rate limiting support
- Market search functionality

### 5. WebSocket Client (`src/polymarket/websocket_client.py`)

**Responsibilities:**
- Real-time data streaming
- User trade monitoring
- Market updates
- Ticker subscriptions

**Key Features:**
- Automatic reconnection with exponential backoff
- Heartbeat mechanism
- Message routing to callbacks
- Subscription management

### 6. Paper Trading (`src/polymarket/paper_trading.py`)

**Responsibilities:**
- Simulate trading without real money
- Track virtual balance
- Calculate P&L
- Persist state to disk

**Key Features:**
- Position tracking
- Average price calculation
- Trade history
- JSON persistence

### 7. Order Executor (`src/polymarket/order_executor.py`)

**Responsibilities:**
- Execute orders (market/limit)
- Validate order parameters
- Route to paper trading or live API
- Return standardized results

**Design Pattern:** Strategy pattern (paper vs live)

### 8. Risk Manager (`src/risk/risk_manager.py`)

**Responsibilities:**
- Pre-trade risk checks
- Position size validation
- Daily limit tracking
- Emergency stop mechanism

**Risk Checks:**
- Max bet size
- Balance sufficiency
- Balance threshold
- Daily trade limit
- Daily loss limit

### 9. Data Aggregator (`src/utils/data_aggregator.py`)

**Responsibilities:**
- Fetch Bitcoin price data
- Aggregate into time intervals
- Provide OHLCV data
- Cache recent data

**Data Sources:**
- Binance
- Coinbase
- Other CCXT exchanges

### 10. Trend Analysis Mode (`src/modes/trend_analysis.py`)

**Responsibilities:**
- Calculate technical indicators
- Generate trading signals
- Execute trades based on signals
- Run analysis loop

**Indicators:**
- EMA (Exponential Moving Average)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)

**Trading Logic:**
- Signal generation based on indicator crossovers
- Duplicate signal prevention
- Periodic analysis (15 min default)

### 11. Copy Trading Mode (`src/modes/copy_trading.py`)

**Responsibilities:**
- Monitor target user trades
- Replicate trades in real-time
- Scale position sizes
- Track processed trades

**Key Features:**
- WebSocket-based monitoring
- Sub-second replication
- Position scaling
- Duplicate trade prevention

## Data Flow

### Trend Analysis Mode

```
1. Timer triggers (every 15 minutes)
2. Data Aggregator fetches Bitcoin price from exchange
3. Trend Analyzer calculates indicators (EMA, RSI, MACD)
4. Signal Generator produces BUY/SELL/HOLD signal
5. Risk Manager validates trade parameters
6. Order Executor places order (paper or live)
7. Logger records trade
8. Risk Manager updates statistics
```

### Copy Trading Mode

```
1. WebSocket receives user trade event
2. Copy Trading Mode validates event
3. Trade parameters extracted and scaled
4. Risk Manager validates trade
5. Order Executor replicates trade (paper or live)
6. Logger records trade
7. Risk Manager updates statistics
```

## Design Patterns

### 1. Strategy Pattern
- **Where:** Order Executor (paper vs live trading)
- **Why:** Allows switching between paper and live trading without changing code

### 2. Observer Pattern
- **Where:** WebSocket callbacks
- **Why:** Decouples WebSocket events from trade execution

### 3. Factory Pattern
- **Where:** Trading mode initialization
- **Why:** Creates appropriate mode based on configuration

### 4. Singleton Pattern
- **Where:** Configuration, Logger
- **Why:** Single source of truth for configuration and logging

## Error Handling

### Levels of Error Handling

1. **Component Level:**
   - Each component handles its own errors
   - Returns error status in results
   - Logs errors appropriately

2. **Mode Level:**
   - Catches component errors
   - Implements retry logic
   - Continues operation when possible

3. **Main Controller Level:**
   - Catches fatal errors
   - Performs cleanup
   - Logs final state

### Recovery Strategies

- **WebSocket disconnection:** Automatic reconnection with exponential backoff
- **API errors:** Logged and skipped, operation continues
- **Price data unavailable:** Wait and retry
- **Risk check failure:** Trade blocked, operation continues

## Concurrency

### Async/Await Pattern

The bot uses Python's `asyncio` for concurrent operations:

- **Trend Analysis:** Periodic async loop
- **Copy Trading:** WebSocket listener runs continuously
- **Heartbeat:** Separate async task for WebSocket keepalive

### Thread Safety

- No explicit threading used
- All operations are async
- State is managed within single event loop

## Data Persistence

### Configuration Files
- `config.yaml`: Bot configuration (version controlled)
- `.env`: Secrets (not version controlled)

### Runtime Data
- `paper_trades.json`: Paper trading state
- `logs/*.log`: Daily log files
- `logs/trades_*.jsonl`: Trade history (JSON Lines)

### Data Format

**Trade Log (JSONL):**
```json
{
  "timestamp": "2026-01-07T10:15:02",
  "mode": "trend_analysis",
  "market": "btc_15min",
  "market_name": "Bitcoin 15min Up/Down",
  "side": "buy",
  "size": 200,
  "price": 0.5,
  "result": "success",
  "paper_trade": true,
  "reason": "Bullish EMA crossover",
  "indicators": {...}
}
```

## Security Considerations

### Credentials
- Private keys stored in `.env` (not committed)
- Environment variables loaded at startup
- No credentials in logs

### API Keys
- Optional for price data
- Required only for live trading
- Validated before use

### Risk Controls
- Multiple layers of validation
- Pre-trade checks
- Position limits
- Emergency stop mechanism

## Performance Considerations

### Optimization Strategies

1. **Data Caching:**
   - Price data cached in memory
   - Indicators calculated once per interval
   - WebSocket messages processed immediately

2. **Rate Limiting:**
   - CCXT handles exchange rate limits
   - py-clob-client handles Polymarket limits
   - Configurable analysis intervals

3. **Memory Management:**
   - Limited historical data storage
   - Processed trade IDs pruned periodically
   - Log rotation prevents disk fill

### Scalability

**Current Design:**
- Single bot instance
- Single trading mode at a time
- Single target user for copy trading

**Future Enhancements:**
- Multiple mode support
- Multiple target users
- Portfolio management
- Multi-market trading

## Testing Strategy

### Manual Testing
- Paper trading mode for strategy testing
- Configuration validation
- Error scenario testing

### Recommended Test Cases

1. **Paper Trading:**
   - Run for 24 hours
   - Verify trade execution
   - Check P&L calculations
   - Validate risk controls

2. **Configuration:**
   - Test different indicator settings
   - Test risk limit enforcement
   - Test mode switching

3. **Error Handling:**
   - Simulate network failures
   - Test with invalid credentials
   - Test with missing market data

## Deployment

### Requirements
- Python 3.9+
- Internet connection
- API credentials (for live trading)

### Recommended Setup
- Linux/Unix environment
- Virtual environment
- Process manager (systemd, supervisor)
- Log monitoring

### Production Checklist
- [ ] Test thoroughly in paper trading mode
- [ ] Set conservative risk limits
- [ ] Configure proper logging
- [ ] Setup monitoring/alerts
- [ ] Backup configuration
- [ ] Document custom settings
- [ ] Test graceful shutdown
- [ ] Plan for updates/maintenance

## Monitoring and Maintenance

### Key Metrics
- Trade success rate
- P&L over time
- Risk limit hits
- Error frequency
- WebSocket uptime (copy trading)

### Maintenance Tasks
- Review logs daily
- Monitor balance
- Check for errors
- Update dependencies
- Backup configuration
- Review performance

## Future Enhancements

### Potential Features
1. **Multi-market support:** Trade multiple markets simultaneously
2. **Advanced strategies:** More complex trading algorithms
3. **Backtesting:** Test strategies on historical data
4. **Web dashboard:** Real-time monitoring UI
5. **Notifications:** Email/SMS alerts for trades
6. **Portfolio management:** Manage multiple positions
7. **Machine learning:** ML-based signal generation
8. **API endpoint:** Control bot via REST API

### Architecture Changes
- Event-driven architecture for multi-mode support
- Database for trade history (instead of JSONL)
- Microservices for scalability
- Message queue for trade execution

## Conclusion

The Polymarket Trading Bot is designed with:
- **Modularity:** Easy to extend and modify
- **Safety:** Multiple layers of risk management
- **Reliability:** Error handling and recovery
- **Flexibility:** Paper trading and multiple modes
- **Observability:** Comprehensive logging

The architecture supports both learning (paper trading) and production use (live trading) while maintaining safety and reliability.

