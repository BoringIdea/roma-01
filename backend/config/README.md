# ROMA-01 Trading Configuration Guide

This directory contains configuration files for the ROMA-01 trading platform.

## ⚠️ Configuration Update

**The platform now uses Account-Centric Configuration** - all configuration is in `trading_config.yaml`.

See **[README_CONFIG.md](README_CONFIG.md)** for the new configuration guide.

## Quick Start

1. Edit `trading_config.yaml` and fill in your accounts/models/agents
2. Set environment variables in `.env` file
3. Start the platform

See **[QUICK_START.md](QUICK_START.md)** for step-by-step instructions.

## Directory Structure

```
config/
├── README.md                           # This file (legacy documentation)
├── README_CONFIG.md                    # New configuration guide (RECOMMENDED)
├── QUICK_START.md                      # Quick start guide
└── trading_config.yaml                 # Main configuration file (all-in-one)
```

## ⚠️ Legacy Documentation

The content below describes the **old configuration format**. 

**For new setups, use the Account-Centric Configuration** - see `README_CONFIG.md`.

---

## Legacy: Global Configuration (`trading_config.yaml`)

> **Note:** This section describes the old format. The new format uses accounts/models/agents segments.

This file controls system-wide settings that apply to all trading agents.

### System Settings

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `system.scan_interval_minutes` | Integer | How often each agent scans the market and makes decisions (in minutes) | 3 |
| `system.max_concurrent_agents` | Integer | Maximum number of agents that can run simultaneously | 6 |
| `system.log_level` | String | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |

### API Settings

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `api.host` | String | API server host address | 0.0.0.0 |
| `api.port` | Integer | API server port | 8080 |

### Agent Configuration

The `agents` array defines which trading agents are active:

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `id` | String | Unique identifier for the agent | Yes |
| `name` | String | Display name for the agent | Yes |
| `enabled` | Boolean | Whether this agent should run | Yes |
| `config_file` | String | Path to the model-specific config file | Yes |

## Model-Specific Configuration

Each model has its own YAML configuration file in the `models/` directory. These files control the behavior of individual trading agents.

### Agent Section

Defines basic agent information.

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `agent.id` | String | Unique identifier (must match trading_config.yaml) | `deepseek-chat-v3.1` |
| `agent.name` | String | Display name shown in UI | `DEEPSEEK CHAT V3.1` |
| `agent.description` | String | Human-readable description of the agent | `DeepSeek V3.1 trading agent` |

### LLM Section

Configures the AI model that powers the trading decisions.

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `llm.provider` | String | LLM provider name | `deepseek`, `anthropic`, `qwen`, `xai`, `google`, `openai` |
| `llm.api_key` | String | API key for the LLM (use environment variables) | `${DEEPSEEK_API_KEY}` |
| `llm.model` | String | Specific model name to use | `deepseek-chat`, `claude-sonnet-4.5`, `qwen-max` |
| `llm.temperature` | Float | Controls randomness in AI responses (0.0-1.0) | `0.15` (low = more conservative) |
| `llm.max_tokens` | Integer | Maximum tokens in AI response | `4000` |

**Temperature Guide:**
- `0.0-0.2`: Very deterministic, conservative trading decisions
- `0.2-0.5`: Balanced approach
- `0.5-1.0`: More creative, potentially more aggressive (not recommended for trading)

### Exchange Section

Configures the connection to the trading exchange (Aster DEX).

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `exchange.type` | String | Exchange type (currently only "aster" supported) | `aster` |
| `exchange.user` | String | Main wallet address (ERC20) | `${ASTER_USER_DEEPSEEK}` |
| `exchange.signer` | String | API wallet address for signing transactions | `${ASTER_SIGNER_DEEPSEEK}` |
| `exchange.private_key` | String | Private key for the signer wallet | `${ASTER_PRIVATE_KEY_DEEPSEEK}` |
| `exchange.testnet` | Boolean | Whether to use testnet (false for production) | `false` |

**Important:** Each model should use its own dedicated trading account for proper isolation and tracking.

### Strategy Section

Controls trading behavior and risk management.

#### Basic Strategy Settings

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `strategy.initial_balance` | Float | Starting balance for performance tracking (USDT) | `10000.0` |
| `strategy.scan_interval_minutes` | Integer | Market scan frequency (overrides global setting if present) | `3` |
| `strategy.max_account_usage_pct` | Integer | Maximum percentage of account to use for trading | `100` |
| `strategy.trading_style` | String | Trading personality: `conservative`, `balanced`, or `aggressive` | `balanced` |

**Trading Styles:**
- **Conservative**: Lower position sizes, stricter risk limits, fewer trades
- **Balanced**: Moderate risk-reward approach
- **Aggressive**: Larger positions, higher leverage usage, more active trading

#### Default Coins

List of trading pairs the agent will analyze and trade.

```yaml
default_coins:
  - "BTCUSDT"     # Bitcoin
  - "ETHUSDT"     # Ethereum
  - "SOLUSDT"     # Solana
  - "BNBUSDT"     # Binance Coin
  - "DOGEUSDT"    # Dogecoin
  - "XRPUSDT"     # Ripple
```

**Supported Coins:**
- High liquidity pairs recommended: BTC, ETH, SOL, BNB
- Alternative coins: DOGE, XRP
- You can add/remove coins based on market conditions

#### Risk Management Settings

Critical parameters that control position sizing and risk exposure.

| Parameter | Type | Description | Recommended Range |
|-----------|------|-------------|-------------------|
| `risk_management.max_positions` | Integer | Maximum number of concurrent open positions | `2-5` |
| `risk_management.max_leverage` | Integer | Maximum leverage multiplier for any position | `5-10` |
| `risk_management.max_position_size_pct` | Integer | Max % of account for a single position | `20-30` |
| `risk_management.max_total_position_pct` | Integer | Max % of account used across all positions | `70-80` |
| `risk_management.max_single_trade_pct` | Integer | Max % of available balance for opening new position (no existing positions) | `40-50` |
| `risk_management.max_single_trade_with_positions_pct` | Integer | Max % of available balance for opening new position (with existing positions) | `25-30` |
| `risk_management.max_daily_loss_pct` | Integer | Max % loss in a day before stopping trading | `10-15` |
| `risk_management.stop_loss_pct` | Integer | Automatic stop loss percentage from entry price | `2-5` |
| `risk_management.take_profit_pct` | Integer | Target profit percentage for closing positions | `8-15` |

**Risk Management Guidelines:**

1. **Position Limits:**
   - `max_positions`: Controls diversification. 3 is recommended for $10k accounts.
   - `max_leverage`: Higher leverage = higher risk. 10x is aggressive, 5x is moderate.

2. **Position Sizing:**
   - `max_position_size_pct`: Prevents over-concentration in a single trade
   - `max_total_position_pct`: Keeps some capital in reserve
   - Conservative: 25% / 75%
   - Balanced: 30% / 80%
   - Aggressive: 35% / 85%

3. **Entry Controls:**
   - `max_single_trade_pct`: Controls initial position entry size
   - `max_single_trade_with_positions_pct`: More conservative when already in positions
   - Ensures averaging prevents account depletion

4. **Exit Controls:**
   - `stop_loss_pct`: Limits maximum loss per trade
   - `take_profit_pct`: Defines profit targets
   - Recommended risk-reward ratio: at least 1:2 (stop_loss : take_profit)

5. **Daily Loss Protection:**
   - `max_daily_loss_pct`: Circuit breaker to stop trading on bad days
   - Prevents emotional revenge trading

## Configuration Examples by Risk Profile

### Conservative Profile
```yaml
risk_management:
  max_positions: 2
  max_leverage: 5
  max_position_size_pct: 25
  max_total_position_pct: 75
  max_single_trade_pct: 40
  max_single_trade_with_positions_pct: 25
  max_daily_loss_pct: 10
  stop_loss_pct: 3
  take_profit_pct: 10
```

### Balanced Profile
```yaml
risk_management:
  max_positions: 3
  max_leverage: 10
  max_position_size_pct: 30
  max_total_position_pct: 80
  max_single_trade_pct: 50
  max_single_trade_with_positions_pct: 30
  max_daily_loss_pct: 15
  stop_loss_pct: 3
  take_profit_pct: 10
```

### Aggressive Profile
```yaml
risk_management:
  max_positions: 5
  max_leverage: 10
  max_position_size_pct: 35
  max_total_position_pct: 85
  max_single_trade_pct: 60
  max_single_trade_with_positions_pct: 35
  max_daily_loss_pct: 20
  stop_loss_pct: 2
  take_profit_pct: 15
```

## Environment Variables

All sensitive credentials are stored in environment variables referenced in the config files:

### LLM API Keys
```bash
DEEPSEEK_API_KEY=your_deepseek_key
QWEN_API_KEY=your_qwen_key
ANTHROPIC_API_KEY=your_anthropic_key
XAI_API_KEY=your_xai_key
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
```

### Exchange Credentials (Per Model)
```bash
# DeepSeek Account
ASTER_USER_DEEPSEEK=0x...
ASTER_SIGNER_DEEPSEEK=0x...
ASTER_PRIVATE_KEY_DEEPSEEK=...

# Qwen Account
ASTER_USER_QWEN=0x...
ASTER_SIGNER_QWEN=0x...
ASTER_PRIVATE_KEY_QWEN=...

# Claude Account
ASTER_USER_CLAUDE=0x...
ASTER_SIGNER_CLAUDE=0x...
ASTER_PRIVATE_KEY_CLAUDE=...

# Grok Account
ASTER_USER_GROK=0x...
ASTER_SIGNER_GROK=0x...
ASTER_PRIVATE_KEY_GROK=...

# Gemini Account
ASTER_USER_GEMINI=0x...
ASTER_SIGNER_GEMINI=0x...
ASTER_PRIVATE_KEY_GEMINI=...

# GPT Account
ASTER_USER_GPT=0x...
ASTER_SIGNER_GPT=0x...
ASTER_PRIVATE_KEY_GPT=...
```

## How to Modify Configurations

### Adding a New Model

1. Create a new YAML file in `config/models/`:
```yaml
# config/models/my-new-model.yaml
agent:
  id: "my-new-model"
  name: "MY NEW MODEL"
  description: "Description of your model"

llm:
  provider: "openai"  # or your provider
  api_key: "${MY_MODEL_API_KEY}"
  model: "gpt-4"
  temperature: 0.15
  max_tokens: 4000

exchange:
  type: "aster"
  user: "${ASTER_USER_MY_MODEL}"
  signer: "${ASTER_SIGNER_MY_MODEL}"
  private_key: "${ASTER_PRIVATE_KEY_MY_MODEL}"
  testnet: false

strategy:
  initial_balance: 10000.0
  scan_interval_minutes: 3
  max_account_usage_pct: 100
  
  default_coins:
    - "BTCUSDT"
    - "ETHUSDT"
    - "SOLUSDT"
    - "BNBUSDT"
    - "DOGEUSDT"
    - "XRPUSDT"
  
  risk_management:
    max_positions: 3
    max_leverage: 10
    max_position_size_pct: 30
    max_total_position_pct: 80
    max_single_trade_pct: 50
    max_single_trade_with_positions_pct: 30
    max_daily_loss_pct: 15
    stop_loss_pct: 3
    take_profit_pct: 10
  
  trading_style: "balanced"
```

2. Add the agent to `trading_config.yaml`:
```yaml
agents:
  - id: "my-new-model"
    name: "MY NEW MODEL"
    enabled: true
    config_file: "config/models/my-new-model.yaml"
```

3. Set up environment variables in `.env` file

4. Restart the backend service

### Adjusting Risk Parameters

To make an agent more conservative:
- Decrease `max_leverage` (e.g., from 10 to 5)
- Decrease `max_position_size_pct` (e.g., from 30 to 25)
- Increase `stop_loss_pct` (e.g., from 3 to 5)
- Decrease `max_positions` (e.g., from 3 to 2)

To make an agent more aggressive:
- Increase `max_leverage` (e.g., from 10 to 15)
- Increase `max_position_size_pct` (e.g., from 30 to 35)
- Decrease `stop_loss_pct` (e.g., from 3 to 2)
- Increase `take_profit_pct` (e.g., from 10 to 15)

### Changing Trading Pairs

Edit the `default_coins` list in the model config:

```yaml
default_coins:
  - "BTCUSDT"    # Always include BTC for market reference
  - "ETHUSDT"    # Major alt coin
  - "SOLUSDT"    # Your choice of additional pairs
  - "DOGEUSDT"   # Meme coins (higher volatility)
```

**Note:** Ensure the pairs are available on Aster DEX before adding them.

## Best Practices

1. **Start Conservative:** Begin with conservative settings and gradually adjust based on performance
2. **Test First:** Use a small `initial_balance` to test new configurations
3. **Monitor Closely:** Watch agent performance for the first few days after config changes
4. **Separate Accounts:** Always use separate exchange accounts for each model
5. **Risk Control:** Never set `max_daily_loss_pct` above 20%
6. **Leverage Caution:** Higher leverage amplifies both gains and losses
7. **Diversification:** Use `max_positions` > 1 to avoid over-concentration
8. **Regular Review:** Review and adjust risk parameters based on market conditions

## Troubleshooting

### Agent Not Starting
- Check that `enabled: true` in `trading_config.yaml`
- Verify environment variables are set correctly
- Check logs for API key or exchange connection errors

### No Trades Being Made
- Verify `default_coins` list has valid trading pairs
- Check if `max_daily_loss_pct` threshold has been reached
- Review risk parameters - they might be too conservative
- Check available balance is sufficient for minimum order sizes

### Too Many Losses
- Reduce `max_leverage`
- Increase `stop_loss_pct`
- Reduce `max_position_size_pct`
- Consider switching `trading_style` to `conservative`

### Configuration Not Applied
- Restart the backend service after making changes
- Check YAML syntax is valid (use a YAML validator)
- Ensure file paths in `trading_config.yaml` are correct

## Support

For detailed setup instructions, see:
- `/backend/ACCOUNT_SETUP.md` - Exchange account configuration
- `/README.md` - General platform documentation
- `/docs/` - Additional documentation

