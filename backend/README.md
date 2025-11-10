# ROMA Trading Backend

Python backend for ROMA Trading Platform powered by FastAPI, DSPy, and multiple LLM integrations.

## Quick Start

```bash
# Setup
./setup.sh

# Configure credentials
cp .env.example .env
nano .env  # Add your API keys and DEX account credentials

# Configure trading agents
cd config
# Edit trading_config.yaml to set up your accounts, models, and agents
# See README_CONFIG.md for detailed instructions

# Start server
./start.sh
```

Server runs on `http://localhost:8080`

## Architecture

```
backend/
├── config/                    # Configuration files
│   ├── README_CONFIG.md       # Detailed configuration guide
│   ├── QUICK_START.md         # Quick start guide
│   ├── trading_config.yaml    # Main configuration (account-centric)
│   └── .env.example           # Environment variables template
├── src/
│   └── roma_trading/
│       ├── agents/            # Trading agents
│       ├── api/               # FastAPI endpoints
│       ├── core/              # Core modules (chat, logging, etc.)
│       ├── config/            # Settings
│       └── toolkits/          # DEX & TA integrations
│           ├── base_dex.py    # Base DEX interface
│           ├── aster_toolkit.py      # Aster DEX implementation
│           └── hyperliquid_toolkit.py # Hyperliquid DEX implementation
├── logs/                      # Trading logs
└── tests/                     # Test files
```

### Account-Centric Architecture

The platform uses an **account-centric** architecture:
- **Accounts**: Define DEX accounts (Aster, Hyperliquid, etc.) independently
- **Models**: Define LLM models (DeepSeek, Qwen, Claude, etc.) independently
- **Agents**: Bind accounts + models + strategies together at runtime

This allows flexible combinations: any account can pair with any model, and multiple agents can share accounts or use different ones.

## Key Features

- **Multi-Agent System**: Run multiple AI agents simultaneously, each with independent account and model
- **Account-Centric Architecture**: Decouple DEX accounts from LLM models for flexible combinations
- **Multi-DEX Support**: 
  - **Aster DEX**: Web3 perpetual futures trading with EIP-191 signing
  - **Hyperliquid DEX**: Direct integration with Hyperliquid perpetual futures
- **DSPy Integration**: Structured AI reasoning with Chain-of-Thought
- **Technical Analysis**: RSI, MACD, EMA, ATR, Bollinger Bands
- **Risk Management**: 4-layer protection system with configurable limits
- **Real-time API**: REST + WebSocket endpoints
- **Performance Tracking**: Win rate, Sharpe ratio, profit factor, equity curves
- **AI Chat Assistant**: Interactive chat for trading advice and prompt suggestions

## API Endpoints

### Agents
- `GET /api/agents` - List all agents
- `GET /api/agents/{id}` - Get agent status
- `GET /api/agents/{id}/account` - Account balance
- `GET /api/agents/{id}/positions` - Current positions
- `GET /api/agents/{id}/performance` - Performance metrics
- `GET /api/agents/{id}/decisions` - Decision history
- `GET /api/agents/{id}/trades` - Trade history
- `GET /api/agents/{id}/equity-history` - Equity curve

### Market
- `GET /api/market/prices` - Current market prices

### Chat
- `POST /api/chat` - AI chat assistant for trading advice

### WebSocket
- `WS /ws/agents/{id}` - Real-time agent updates

Full API docs: http://localhost:8080/docs

## Configuration

See [config/README_CONFIG.md](config/README_CONFIG.md) for detailed configuration guide.

### Configuration Structure

The platform uses an **account-centric** configuration in `config/trading_config.yaml`:

```yaml
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

agents:
  - id: "deepseek-aster-01"
    account_id: "aster-acc-01"
    model_id: "deepseek-v3.1"
    enabled: true
```

### Supported DEXs
- **Aster Finance**: Web3 DEX with EIP-191 signing
- **Hyperliquid**: Perpetual futures DEX

### Supported LLMs
- DeepSeek (recommended)
- Qwen
- Claude (Anthropic)
- Grok (xAI)
- Gemini (Google)
- GPT (OpenAI)

### Trading Pairs
BTC, ETH, SOL, BNB, DOGE, XRP (all paired with USDT)

## Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest

# Start with debug logging
LOG_LEVEL=DEBUG python -m roma_trading.main
```

## Documentation

- **[ACCOUNT_SETUP.md](ACCOUNT_SETUP.md)** - Account setup guide (start here!)
- **[config/README_CONFIG.md](config/README_CONFIG.md)** - Complete configuration reference
- **[config/QUICK_START.md](config/QUICK_START.md)** - Step-by-step setup guide
- **[../docs/](../docs/)** - Full documentation (architecture, API, etc.)

## Requirements

- Python 3.12 or 3.13 (**NOT 3.14**)
- LLM API key (DeepSeek recommended)
- DEX account credentials:
  - **Aster DEX**: `user`, `signer`, `private_key`
  - **Hyperliquid DEX**: `api_secret` (API wallet private key), `account_id` (main wallet address)

## Account Setup

1. **Create `.env` file** with your API keys and DEX credentials:
   ```bash
   cp .env.example .env
   # Edit .env and add your credentials
   ```

2. **Configure `config/trading_config.yaml`**:
   - Define your accounts (Aster or Hyperliquid)
   - Define your models (DeepSeek, Qwen, etc.)
   - Create agents that bind accounts + models

3. **See [ACCOUNT_SETUP.md](ACCOUNT_SETUP.md)** for detailed setup instructions.

## Support

For issues and questions:
- Check [ACCOUNT_SETUP.md](ACCOUNT_SETUP.md) troubleshooting section
- Review logs in `logs/` directory
- See [../docs/](../docs/) for detailed documentation

