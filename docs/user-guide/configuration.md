# Configuration Guide

Complete guide to configuring the ROMA Trading Platform with account-centric architecture and multi-DEX support.

---

## 📋 Table of Contents

1. [Account-Centric Architecture](#account-centric-architecture)
2. [Environment Variables](#environment-variables)
3. [Trading Configuration](#trading-configuration)
4. [DEX Account Configuration](#dex-account-configuration)
5. [Model Configuration](#model-configuration)
6. [Agent Configuration](#agent-configuration)
7. [Risk Management](#risk-management)
8. [Advanced Settings](#advanced-settings)

---

## 🏗️ Account-Centric Architecture

ROMA-01 uses an **account-centric** configuration model that decouples DEX accounts from LLM models, allowing flexible combinations:

- **Accounts**: Define DEX trading accounts (Aster, Hyperliquid, etc.)
- **Models**: Define LLM configurations (DeepSeek, Qwen, Claude, etc.)  
- **Agents**: Bind accounts with models to create trading agents

This architecture enables:
- ✅ Mix and match any account with any model
- ✅ Run multiple agents on the same DEX with different models
- ✅ Run multiple agents on different DEXs simultaneously
- ✅ Each agent can have custom prompts and strategy

See [backend/config/README_CONFIG.md](../../backend/config/README_CONFIG.md) for detailed configuration guide.

---

## 🔐 Environment Variables

### Backend Configuration (`backend/.env`)

```bash
# LLM Providers
DEEPSEEK_API_KEY=your_deepseek_api_key
QWEN_API_KEY=your_qwen_api_key
OPENROUTER_API_KEY=your_openrouter_api_key  # Optional

# Aster DEX Configuration
ASTER_USER_01=0xYourUserAddress
ASTER_SIGNER_01=0xYourSignerAddress
ASTER_PRIVATE_KEY_01=your_private_key

# Hyperliquid DEX Configuration (Optional)
HL_SECRET_KEY_01=your_hyperliquid_secret_key
HL_ACCOUNT_ADDRESS_01=0xYourHyperliquidAddress

# Optional: Testnet
# ASTER_TESTNET=true
```

### Required Keys

#### 1. DeepSeek API Key
- Sign up at: https://platform.deepseek.com
- Navigate to API Keys section
- Create new API key
- Copy to `.env`

#### 2. Aster DEX Credentials
- **User Address**: Your wallet address
- **Signer Address**: Authorized signer address
- **Private Key**: For signing transactions (keep secure!)

#### 3. Hyperliquid DEX Credentials (Optional)
- **API Secret**: Secret key for Hyperliquid API authentication
- **Account Address**: Your Hyperliquid account address

⚠️ **Security**: Never commit `.env` to version control!

---

## 🎯 Trading Configuration

### Main Config (`backend/config/trading_config.yaml`)

The configuration uses account-centric architecture with three main sections:

```yaml
# System Settings
system:
  scan_interval_minutes: 3        # How often agents make decisions
  max_concurrent_agents: 6        # Maximum number of agents
  log_level: "INFO"               # DEBUG, INFO, WARNING, ERROR

# API Settings
api:
  host: "0.0.0.0"                 # API server host
  port: 8080                      # API server port

# DEX Accounts
accounts:
  - id: "aster-acc-01"
    dex_type: "aster"
    user: ${ASTER_USER_01}
    signer: ${ASTER_SIGNER_01}
    private_key: ${ASTER_PRIVATE_KEY_01}
    testnet: false
    hedge_mode: false
  
  - id: "hl-acc-01"
    dex_type: "hyperliquid"
    api_secret: ${HL_SECRET_KEY_01}
    account_id: ${HL_ACCOUNT_ADDRESS_01}
    testnet: false

# LLM Models
models:
  - id: "deepseek-v3.1"
    provider: "deepseek"
    api_key: ${DEEPSEEK_API_KEY}
    model: "deepseek-chat"
    temperature: 0.15
    max_tokens: 4000
  
  - id: "qwen3-max"
    provider: "qwen"
    api_key: ${QWEN_API_KEY}
    model: "qwen-max"
    temperature: 0.15
    max_tokens: 4000

# Trading Agents (bind accounts with models)
agents:
  - id: "deepseek-aster-01"
    name: "DeepSeek on Aster-01"
    enabled: true
    account_id: "aster-acc-01"
    model_id: "deepseek-v3.1"
  
  - id: "qwen-hl-01"
    name: "Qwen on Hyperliquid-01"
    enabled: false
    account_id: "hl-acc-01"
    model_id: "qwen3-max"
```

### Configuration Options

| Option | Description | Default | Recommended |
|--------|-------------|---------|-------------|
| `scan_interval_minutes` | Decision cycle frequency | 3 | 3-5 min |
| `max_concurrent_agents` | Max parallel agents | 5 | 1-3 |
| `log_level` | Logging verbosity | INFO | INFO (prod), DEBUG (dev) |

---

## 🌐 DEX Account Configuration

### Aster Account

```yaml
accounts:
  - id: "aster-acc-01"
    dex_type: "aster"
    user: ${ASTER_USER_01}          # Wallet address
    signer: ${ASTER_SIGNER_01}      # Authorized signer
    private_key: ${ASTER_PRIVATE_KEY_01}  # For EIP-191 signing
    testnet: false
    hedge_mode: false
```

### Hyperliquid Account

```yaml
accounts:
  - id: "hl-acc-01"
    dex_type: "hyperliquid"
    api_secret: ${HL_SECRET_KEY_01}        # Secret key for API
    account_id: ${HL_ACCOUNT_ADDRESS_01}   # Account address
    testnet: false
```

## 🧠 Model Configuration

### Model Config Template

```yaml
models:
  - id: "deepseek-v3.1"
    provider: "deepseek"
    api_key: ${DEEPSEEK_API_KEY}
    model: "deepseek-chat"
    temperature: 0.15
    max_tokens: 4000
```

## 🤖 Agent Configuration

### Agent Config Template

```yaml
# Agent binds account and model
agents:
  - id: "deepseek-aster-01"
    name: "DeepSeek on Aster-01"
    enabled: true
    account_id: "aster-acc-01"      # Reference to account above
    model_id: "deepseek-v3.1"       # Reference to model above
    
    # Optional: Agent-specific strategy overrides
    strategy:
      initial_balance: 10000.0          # For display/calculations
      scan_interval_minutes: 3          # Decision frequency
      
      # Trading Pairs
      default_coins:
        - "BTCUSDT"
        - "ETHUSDT"
        - "SOLUSDT"
        - "BNBUSDT"
      
      # Risk Management
      risk_management:
        max_positions: 3                # Max concurrent positions
        max_leverage: 10                # Max leverage per position
        max_position_size_pct: 30       # Single position max % of account
        max_total_position_pct: 80      # Total positions max % of balance
        max_single_trade_pct: 50        # Max % per trade (no positions)
        max_single_trade_with_positions_pct: 30  # Max % (with positions)
        max_daily_loss_pct: 15          # Daily loss limit
        stop_loss_pct: 3                # Per-position stop loss
        take_profit_pct: 10             # Per-position take profit
      
      # Trading Style
      trading_style: "aggressive"       # aggressive, conservative, balanced
```

---

## ⚖️ Risk Management

### Risk Layers

#### Layer 1: Single Trade Limits
- **No positions**: Max 50% of available balance
- **With positions**: Max 30% of available balance

```yaml
risk_management:
  max_single_trade_pct: 50
  max_single_trade_with_positions_pct: 30
```

#### Layer 2: Total Position Limit
- **All positions combined**: Max 80% of total balance

```yaml
risk_management:
  max_total_position_pct: 80
```

#### Layer 3: Per-Position Limits
- **Single position**: Max 30% of account
- **Stop loss**: 3% from entry
- **Take profit**: 10% from entry

```yaml
risk_management:
  max_position_size_pct: 30
  stop_loss_pct: 3
  take_profit_pct: 10
```

#### Layer 4: Daily Limits
- **Daily loss**: Max 15% of starting balance

```yaml
risk_management:
  max_daily_loss_pct: 15
```

### Risk Profiles

#### Aggressive
```yaml
max_positions: 3
max_leverage: 10
max_position_size_pct: 30
max_total_position_pct: 80
stop_loss_pct: 3
take_profit_pct: 10
```

#### Conservative
```yaml
max_positions: 2
max_leverage: 5
max_position_size_pct: 15
max_total_position_pct: 60
stop_loss_pct: 2
take_profit_pct: 8
```

#### Balanced
```yaml
max_positions: 3
max_leverage: 7
max_position_size_pct: 20
max_total_position_pct: 70
stop_loss_pct: 2.5
take_profit_pct: 9
```

---

## 🧠 Model Configuration

### LLM Providers

#### DeepSeek (Recommended)
```yaml
llm:
  provider: "deepseek"
  api_key: "${DEEPSEEK_API_KEY}"
  model: "deepseek-chat"
  temperature: 0.15
  max_tokens: 4000
```

**Pros**: Fast, cheap, good for trading logic  
**Cons**: Less creative

#### Qwen
```yaml
llm:
  provider: "qwen"
  api_key: "${QWEN_API_KEY}"
  model: "qwen-max"
  temperature: 0.2
  max_tokens: 4000
```

**Pros**: Good reasoning, multilingual  
**Cons**: Slightly slower

#### OpenRouter (Multiple Models)
```yaml
llm:
  provider: "openrouter"
  api_key: "${OPENROUTER_API_KEY}"
  model: "anthropic/claude-3-sonnet"
  temperature: 0.1
  max_tokens: 4000
```

**Pros**: Access to many models  
**Cons**: Higher cost

### Temperature Settings

| Temperature | Behavior | Use Case |
|-------------|----------|----------|
| 0.0 - 0.1 | Very deterministic | Production trading |
| 0.1 - 0.3 | Mostly consistent | Default |
| 0.3 - 0.7 | Balanced | Testing strategies |
| 0.7 - 1.0 | Creative/random | Not recommended |

**Recommendation**: 0.1-0.2 for production

---

## 🎚️ Advanced Settings

### Multi-Agent Setup

When running multiple agents:

**Agent 1 (Aggressive):**
```yaml
max_account_usage_pct: 60  # 60% of available
```

**Agent 2 (Conservative):**
```yaml
max_account_usage_pct: 40  # 40% of available
```

**Total**: 100% allocated, no overlap

### Coin Selection

#### High Balance ($100+)
```yaml
default_coins:
  - "BTCUSDT"    # All coins
  - "ETHUSDT"
  - "SOLUSDT"
  - "BNBUSDT"
```

#### Medium Balance ($20-$100)
```yaml
default_coins:
  - "ETHUSDT"    # Skip BTC (too expensive)
  - "SOLUSDT"
  - "BNBUSDT"
```

#### Low Balance ($5-$20)
```yaml
default_coins:
  - "SOLUSDT"    # Focus on cheap coins
  - "BNBUSDT"
```

### Scan Intervals

| Interval | Behavior | Use Case |
|----------|----------|----------|
| 1 min | Very frequent | Scalping |
| 3 min | Frequent | Day trading (default) |
| 5 min | Moderate | Swing trading |
| 15 min | Infrequent | Position trading |

**Recommendation**: 3-5 minutes for most strategies

### Leverage Settings

⚠️ **Higher leverage = Higher risk**

| Leverage | Risk Level | Use Case |
|----------|------------|----------|
| 2-3x | Low | Conservative |
| 5-7x | Medium | Balanced |
| 8-10x | High | Aggressive |
| 10x+ | Very High | Expert only |

**Recommendation**: Start with 5x, adjust based on experience

---

## 🔄 Configuration Changes

### Applying Changes

1. **Edit configuration file**:
```bash
nano backend/config/trading_config.yaml
# or
nano backend/config/models/deepseek_aggressive.yaml
```

2. **Restart backend**:
```bash
cd backend
# Stop: Ctrl+C
./start.sh
```

3. **Changes take effect immediately**

### Hot Reload

❌ **Not supported** - Requires restart

### Validation

Configuration is validated on startup:
- Missing required fields → Error
- Invalid values → Warning + Default
- Environment variables → Resolved at runtime

---

## 🧪 Testing Configuration

### 1. Testnet Mode

Enable testnet in agent config:
```yaml
exchange:
  testnet: true
```

### 2. Dry Run (Coming Soon)

```yaml
strategy:
  dry_run: true  # Log decisions, don't execute
```

### 3. Small Balance

Start with minimum:
```yaml
risk_management:
  max_position_size_pct: 10  # Very conservative
  max_total_position_pct: 30
```

---

## 📊 Monitoring Configuration

### Log Levels

```yaml
system:
  log_level: "DEBUG"  # More verbose
  log_level: "INFO"   # Default
  log_level: "WARNING"  # Errors only
```

### Decision Logging

All decisions automatically logged to:
```
backend/logs/decisions/{agent_id}/decision_*.json
```

No configuration needed.

---

## 🔐 Security Best Practices

1. **API Keys**:
   - Use `.env` file
   - Never commit to git
   - Rotate regularly

2. **Private Keys**:
   - Store securely
   - Use hardware wallet in production
   - Test with small amounts first

3. **IP Whitelisting**:
   - Configure on Aster DEX
   - Lock to your server IP

4. **Limits**:
   - Start conservative
   - Increase gradually
   - Monitor closely

5. **Monitoring**:
   - Check logs daily
   - Set up alerts
   - Have emergency stop plan

---

## 📝 Configuration Checklist

### First Time Setup
- [ ] Copy `.env.example` to `.env`
- [ ] Add DeepSeek API key
- [ ] Add Aster credentials
- [ ] Review `trading_config.yaml`
- [ ] Check risk management settings
- [ ] Set appropriate leverage limits
- [ ] Choose trading pairs
- [ ] Test on testnet first

### Before Going Live
- [ ] Reduce position limits
- [ ] Lower leverage
- [ ] Set tight stop losses
- [ ] Enable only 1 agent
- [ ] Monitor first 24 hours
- [ ] Review all decisions
- [ ] Verify P/L calculation

### Regular Maintenance
- [ ] Review performance weekly
- [ ] Adjust risk limits as needed
- [ ] Rotate API keys monthly
- [ ] Update models if available
- [ ] Check for updates

---

## 🆘 Common Issues

### "Missing API key"
- Check `.env` file exists
- Verify key format
- Ensure no extra spaces

### "Insufficient balance"
- Reduce position sizes
- Lower leverage
- Check available balance

### "Too many positions"
- Check `max_positions` setting
- Close some positions manually
- Adjust strategy

### Agent not trading
- Check `enabled: true`
- Verify scan interval
- Check logs for errors
- Ensure API keys valid

---

**For more help, see [Troubleshooting Guide](TROUBLESHOOTING.md)**

