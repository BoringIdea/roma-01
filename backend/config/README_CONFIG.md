# ROMA Trading Platform - Configuration Guide

## Quick Start

**New users**: Start by editing the default configuration:
```bash
cd backend/config
# Edit trading_config.yaml and fill in your accounts/models/agents
vim trading_config.yaml  # or use your preferred editor
```

See `QUICK_START.md` for step-by-step instructions.

## Overview

ROMA Trading Platform supports **two configuration styles**:

1. **Legacy Style** (backward compatible): Each agent has its own config file
2. **Account-Centric Style** (new, recommended): Three-segment configuration (accounts/models/agents)

## Configuration Files

- **`trading_config.yaml`** - Main configuration file (all-in-one)
- **`QUICK_START.md`** - Step-by-step setup guide
- **`README_CONFIG.md`** - This file (detailed documentation)

## Configuration Styles

### 1. Legacy Style (Backward Compatible)

Each agent has its own configuration file:

```yaml
# config/trading_config.yaml
agents:
  - id: "deepseek-chat-v3.1"
    name: "DEEPSEEK CHAT V3.1"
    enabled: true
    config_file: "config/models/deepseek-chat-v3.1.yaml"
```

```yaml
# config/models/deepseek-chat-v3.1.yaml
agent:
  id: deepseek-chat-v3.1
  name: DEEPSEEK CHAT V3.1
llm:
  provider: deepseek
  api_key: ${DEEPSEEK_API_KEY}
  model: deepseek-chat
exchange:
  type: aster
  user: ${ASTER_USER_DEEPSEEK}
  signer: ${ASTER_SIGNER_DEEPSEEK}
  private_key: ${ASTER_PRIVATE_KEY_DEEPSEEK}
strategy:
  initial_balance: 10000.0
  # ... strategy config
```

**Pros:**
- Simple, one file per agent
- Easy to understand
- Good for single-agent setups

**Cons:**
- Cannot reuse accounts/models
- Duplication when multiple agents use same account/model
- Harder to manage many agents

### 2. Account-Centric Style (Recommended for Multi-Agent)

Three-segment configuration with references:

```yaml
# config/trading_config.yaml
accounts:
  - id: "aster-acc-01"
    dex_type: "aster"
    user: ${ASTER_USER_01}
    signer: ${ASTER_SIGNER_01}
    private_key: ${ASTER_PRIVATE_KEY_01}
  
  - id: "hl-acc-01"
    dex_type: "hyperliquid"
    api_secret: ${HL_SECRET_KEY_01}
    account_id: ${HL_ACCOUNT_ADDRESS_01}

models:
  - id: "deepseek-v3.1"
    provider: "deepseek"
    api_key: ${DEEPSEEK_API_KEY}
    model: "deepseek-chat"
  
  - id: "qwen3-max"
    provider: "qwen"
    api_key: ${QWEN_API_KEY}
    model: "qwen-max"
    location: "china"  # "china" for China region, "international" or other values for international region

agents:
  - id: "deepseek-aster-01"
    name: "DeepSeek on Aster-01"
    enabled: true
    account_id: "aster-acc-01"  # Reference to accounts
    model_id: "deepseek-v3.1"   # Reference to models
    strategy:
      initial_balance: 10000.0
      # ... strategy config
  
  - id: "deepseek-hl-01"
    name: "DeepSeek on HL-01"
    enabled: false
    account_id: "hl-acc-01"      # Different account
    model_id: "deepseek-v3.1"    # Same model
    strategy:
      initial_balance: 10000.0
```

**Pros:**
- **Reuse accounts**: One account can be used by multiple agents
- **Reuse models**: One model can be used by multiple agents
- **Flexible combinations**: Mix any account with any model
- **Centralized management**: All accounts/models in one place
- **Easy scaling**: Add new agents by just referencing existing accounts/models

**Cons:**
- Slightly more complex setup
- Requires understanding of references

## Key Concepts

### Decoupling Model and DEX

In the account-centric architecture:
- **Models** and **DEX accounts** are **completely decoupled**
- An **agent instance** binds them together
- You can have:
  - Same model on different DEXs (e.g., DeepSeek on Aster + DeepSeek on Hyperliquid)
  - Different models on same DEX (e.g., DeepSeek on Aster + Qwen on Aster)
  - Any combination you want

### Example: 6 Hyperliquid Accounts + 6 Models

```yaml
accounts:
  - id: "hl-acc-01"  # Hyperliquid account 1
  - id: "hl-acc-02"  # Hyperliquid account 2
  - id: "hl-acc-03"  # Hyperliquid account 3
  - id: "hl-acc-04"  # Hyperliquid account 4
  - id: "hl-acc-05"  # Hyperliquid account 5
  - id: "hl-acc-06"  # Hyperliquid account 6

models:
  - id: "deepseek-v3.1"
  - id: "qwen3-max"
  - id: "claude-sonnet-4.5"
  - id: "grok-4"
  - id: "gemini-2.5-pro"
  - id: "gpt-5"

agents:
  - id: "hl-deepseek-01"
    account_id: "hl-acc-01"
    model_id: "deepseek-v3.1"
  - id: "hl-qwen-02"
    account_id: "hl-acc-02"
    model_id: "qwen3-max"
  # ... and so on
```

This allows you to run 6 different models, each on its own Hyperliquid account, all in parallel.

## Account Configuration

### Aster DEX Account

```yaml
accounts:
  - id: "aster-acc-01"
    name: "Aster Account 01"
    dex_type: "aster"
    user: ${ASTER_USER_01}           # Required
    signer: ${ASTER_SIGNER_01}       # Required
    private_key: ${ASTER_PRIVATE_KEY_01}  # Required
    testnet: false                    # Optional, default: false
    hedge_mode: false                 # Optional, default: false
```

### Hyperliquid DEX Account

```yaml
accounts:
  - id: "hl-acc-01"
    name: "Hyperliquid Account 01"
    dex_type: "hyperliquid"
    api_secret: ${HL_SECRET_KEY_01}  # Required: API wallet private key (for signing)
    account_id: ${HL_ACCOUNT_ADDRESS_01}  # Required: MAIN wallet address (for balance query)
    testnet: false                    # Optional, default: false
    hedge_mode: false                 # Optional, default: false
```

**Important for Hyperliquid:**
- `api_secret`: The private key of your **API wallet** (authorized for trading)
- `account_id`: The address of your **MAIN wallet** (the wallet that holds funds)
  
  ⚠️ **Do NOT use the API wallet address here!** Always use your main wallet address.
  
  You can find your main wallet address on https://app.hyperliquid.xyz/
  The API wallet address is derived from the `api_secret` and is used only for signing transactions.

## Model Configuration

```yaml
models:
  - id: "deepseek-v3.1"
    provider: "deepseek"              # Required
    api_key: ${DEEPSEEK_API_KEY}      # Required
    model: "deepseek-chat"            # Required
    temperature: 0.15                 # Optional, default: 0.15
    max_tokens: 4000                  # Optional, default: 4000
  
  - id: "qwen3-max"
    provider: "qwen"                  # Required
    api_key: ${QWEN_API_KEY}          # Required
    model: "qwen-max"                 # Required
    location: "china"                 # Optional, default: "china"
                                      #   - "china": Use https://dashscope.aliyuncs.com/compatible-mode/v1
                                      #   - "international" or other: Use https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    temperature: 0.15                 # Optional, default: 0.15
    max_tokens: 4000                  # Optional, default: 4000
```

Supported providers:
- `deepseek`
- `qwen` (supports `location` parameter for region selection)
- `anthropic`
- `openai`
- `xai`
- `google`

## Agent Configuration

```yaml
agents:
  - id: "agent-id"                    # Required
    name: "Agent Name"                 # Required
    enabled: true                      # Optional, default: true
    account_id: "aster-acc-01"         # Required (account-centric mode)
    model_id: "deepseek-v3.1"         # Required (account-centric mode)
    strategy:                          # Optional, will use defaults if omitted
      initial_balance: 10000.0
      scan_interval_minutes: 3
      max_account_usage_pct: 100
      default_coins:
        - BTCUSDT
        - ETHUSDT
      risk_management:
        max_positions: 3
        max_leverage: 10
        # ... more risk settings
      trading_style: "balanced"
      custom_prompts:
        enabled: false
        # ... custom prompt fields
```

### Strategy Configuration Fields

#### Basic Settings

| Field | Type | Description | Default | Recommended |
|-------|------|-------------|---------|-------------|
| `initial_balance` | Float | Starting balance for performance tracking (USDT). Used for calculations and display, not actual account balance. | `10000.0` | Match your actual balance |
| `scan_interval_minutes` | Integer | How often the agent scans the market and makes trading decisions (in minutes). | `3` | 3-5 minutes |
| `max_account_usage_pct` | Integer | Maximum percentage of account balance to use for trading. Useful when multiple agents share one account. | `100` | 100% for single agent, 60-80% per agent if sharing |

#### Trading Pairs

```yaml
default_coins:
  - BTCUSDT   # Bitcoin
  - ETHUSDT   # Ethereum
  - SOLUSDT   # Solana
  - BNBUSDT   # Binance Coin
  - DOGEUSDT  # Dogecoin
  - XRPUSDT   # Ripple
```

**Supported Trading Pairs:**
- All pairs must end with `USDT` (e.g., `BTCUSDT`, not `BTC`)
- Available pairs depend on the DEX (Aster/Hyperliquid support different sets)
- More pairs = more opportunities but also more complexity

#### Risk Management

| Field | Type | Description | Default | Range |
|-------|------|-------------|---------|-------|
| `max_positions` | Integer | Maximum number of concurrent open positions | `3` | 2-5 |
| `max_leverage` | Integer | Maximum leverage multiplier for any position | `10` | 1-10 (or DEX limit) |
| `max_position_size_pct` | Integer | Maximum % of account balance for a single position | `30` | 20-35 |
| `max_total_position_pct` | Integer | Maximum % of account balance used across ALL positions | `80` | 70-85 |
| `max_single_trade_pct` | Integer | Maximum % of available balance for opening new position when NO positions exist | `50` | 40-60 |
| `max_single_trade_with_positions_pct` | Integer | Maximum % of available balance for opening new position when positions ALREADY exist | `30` | 25-35 |
| `max_daily_loss_pct` | Integer | Maximum % loss in a day before agent stops trading (circuit breaker) | `15` | 10-20 |
| `stop_loss_pct` | Float | Automatic stop loss percentage from entry price | `3.0` | 2.0-5.0 |
| `take_profit_pct` | Float | Target profit percentage for closing positions | `10.0` | 8.0-15.0 |

**Risk Management Explained:**

- **Layer 1 - Single Trade Limits:**
  - No positions: `max_single_trade_pct` (e.g., 50%)
  - With positions: `max_single_trade_with_positions_pct` (e.g., 30%)

- **Layer 2 - Total Position Limit:**
  - All positions combined: `max_total_position_pct` (e.g., 80%)
  - Always keeps 20%+ reserve

- **Layer 3 - Per-Position Limits:**
  - Single position: `max_position_size_pct` (e.g., 30%)
  - Stop loss: `stop_loss_pct` (e.g., 3% from entry)
  - Take profit: `take_profit_pct` (e.g., 10% from entry)

- **Layer 4 - Daily Limits:**
  - Daily loss: `max_daily_loss_pct` (e.g., 15%)
  - Agent stops trading if daily loss exceeds this

#### Trading Style

```yaml
trading_style: "balanced"  # Options: "conservative", "balanced", "aggressive"
```

**Trading Style Profiles:**

| Style | Description | Use Case |
|-------|-------------|----------|
| `conservative` | Lower leverage, smaller positions, tighter stops | Beginners, low balance, risk-averse |
| `balanced` | Moderate settings, good risk/reward | Default, most users |
| `aggressive` | Higher leverage, larger positions, wider stops | Experienced traders, testing strategies |

**Note:** Trading style is informational and may affect AI decision-making. Risk limits are still enforced regardless of style.

#### Custom Prompts

```yaml
custom_prompts:
  enabled: false                      # Enable custom prompts
  trading_philosophy: ""              # Overall trading philosophy (e.g., "Focus on trend following")
  entry_preferences: ""               # Entry signal preferences (e.g., "Wait for RSI < 30")
  position_management: ""             # Position management rules (e.g., "Scale out at 50% profit")
  market_preferences: ""              # Market condition preferences (e.g., "Avoid trading during low volume")
  additional_rules: ""                # Any additional custom rules
```

**Custom Prompts Usage:**

- **Enabled**: Set `enabled: true` to activate custom prompts
- **Integration**: Custom prompts are merged with core trading rules
- **Examples**: 
  - Trading philosophy: "Focus on trend-following strategies during strong market trends"
  - Entry preferences: "Only enter long positions when MACD crosses above signal line"
  - Position management: "Take profits at 5%, 10%, and 15% levels"
  - Market preferences: "Avoid trading during first 30 minutes after market open"
  - Additional rules: "Never trade during major news events"

**Note:** Custom prompts are appended to the core system prompt. They should complement, not contradict, the built-in risk management rules.

### Complete Strategy Example

```yaml
strategy:
  initial_balance: 10000.0
  scan_interval_minutes: 3
  max_account_usage_pct: 100
  
  default_coins:
    - BTCUSDT
    - ETHUSDT
    - SOLUSDT
    - BNBUSDT
    - DOGEUSDT
    - XRPUSDT
  
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

  advanced_orders:
    enable_take_profit: false      # true = Enable take profit
    take_profit_pct: 5.0           # Take profit trigger percentage, based on entry price
    enable_stop_loss: false        # true = Enable stop loss
    stop_loss_pct: 2.0             # Stop loss trigger percentage, based on entry price
  
  trading_style: "balanced"
  
  
  custom_prompts:
    enabled: false
    trading_philosophy: ""
    entry_preferences: ""
    position_management: ""
    market_preferences: ""
    additional_rules: ""
```

### Risk Profile Examples

#### Conservative Profile
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
trading_style: "conservative"
```

#### Balanced Profile (Default)
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
trading_style: "balanced"
```

#### Aggressive Profile
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
trading_style: "aggressive"
```

## Migration from Legacy to Account-Centric

### Step 1: Extract Accounts

From your existing agent configs, identify unique accounts:

```yaml
# Before (legacy)
# config/models/deepseek-chat-v3.1.yaml
exchange:
  type: aster
  user: ${ASTER_USER_DEEPSEEK}
  signer: ${ASTER_SIGNER_DEEPSEEK}
  private_key: ${ASTER_PRIVATE_KEY_DEEPSEEK}

# After (account-centric)
# config/trading_config.yaml
accounts:
  - id: "aster-deepseek"
    dex_type: "aster"
    user: ${ASTER_USER_DEEPSEEK}
    signer: ${ASTER_SIGNER_DEEPSEEK}
    private_key: ${ASTER_PRIVATE_KEY_DEEPSEEK}
```

### Step 2: Extract Models

```yaml
# Before (legacy)
# config/models/deepseek-chat-v3.1.yaml
llm:
  provider: deepseek
  api_key: ${DEEPSEEK_API_KEY}
  model: deepseek-chat

# After (account-centric)
# config/trading_config.yaml
models:
  - id: "deepseek-v3.1"
    provider: "deepseek"
    api_key: ${DEEPSEEK_API_KEY}
    model: "deepseek-chat"
```

### Step 3: Create Agents with References

```yaml
# After (account-centric)
agents:
  - id: "deepseek-aster-01"
    name: "DeepSeek on Aster"
    account_id: "aster-deepseek"
    model_id: "deepseek-v3.1"
    strategy:
      # Copy from legacy config
```

## Best Practices

1. **One Account Per Agent** (for production): Avoid conflicts by using separate accounts
2. **Reuse Models**: Define each model once, use in multiple agents
3. **Use Environment Variables**: Never hardcode secrets in config files
4. **Version Control**: Commit config files, but use `.env` for secrets
5. **Testnet First**: Use `testnet: true` for testing new configurations

## Examples

See:
- `backend/config/trading_config.yaml` - Account-centric style example (current default)
- `backend/config/trading_config.yaml.example` - Template with all fields documented

## Troubleshooting

### Error: "Account not found: xxx"
- Check that `account_id` in agent matches an `id` in `accounts` section
- Ensure account is defined before being referenced

### Error: "Model not found: xxx"
- Check that `model_id` in agent matches an `id` in `models` section
- Ensure model is defined before being referenced

### Error: "Missing required fields"
- Check account has all required fields for its `dex_type`
- Check model has `provider` and `model` fields

### Agent not loading
- Check `enabled: true` (or omit, defaults to true)
- Check logs for specific error messages
- Verify environment variables are set correctly

