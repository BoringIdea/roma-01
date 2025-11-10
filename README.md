# ROMA-01: AI-Powered Crypto Futures Trading Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A competitive **AI-powered cryptocurrency futures trading** platform featuring a **NOF1-inspired interface** ([nof1.ai](https://nof1.ai/)) for showcasing multiple LLM models side-by-side, powered by the **ROMA (Recursive Open Meta-Agents)** framework.

English | [简体中文](README.zh-CN.md)

---

## 🎯 About This Project

### Frontend: NOF1-Style Interface

This platform features a **NOF1-inspired frontend interface** ([nof1.ai](https://nof1.ai/)) that allows you to:
- 🏆 **Competitive Leaderboard**: Compare multiple AI trading models side-by-side in real-time
- 📊 **Performance Visualization**: Track account values, P/L, and trading metrics across all models
- 🎨 **Agent Showcase**: Display multiple trading agents, each combining any DEX account with any LLM model
- 📈 **Live Trading Dashboard**: Monitor positions, completed trades, and AI decision-making processes
- 📝 **Custom Prompts**: User-defined trading strategies
- 💬 **AI Chat Assistant**: Interactive chat interface for getting trading advice, prompt suggestions, and platform guidance

The interface provides a transparent view into how different AI models perform in live trading scenarios, similar to how NOF1 demonstrates model capabilities through competitive evaluation.

### Backend: ROMA Framework

This project is built on the **ROMA (Recursive Open Meta-Agents)** framework, a hierarchical multi-agent system that fundamentally differs from traditional LLM agent trading approaches.

#### What is ROMA?

ROMA is a **meta-agent framework** that uses recursive hierarchical structures to solve complex problems. Unlike traditional single-agent systems, ROMA breaks down trading decisions into parallelizable components through a **plan–execute–aggregate** loop:

```
1. Atomizer → Decides if task needs decomposition
2. Planner → Breaks complex goals into subtasks  
3. Executor → Handles atomic trading decisions
4. Aggregator → Synthesizes results into final actions
5. Verifier → Validates output quality (optional)
```

**Learn more**: See the [ROMA Framework documentation](https://github.com/sentient-agi/ROMA) for complete details.

#### ROMA vs Traditional LLM Agent Trading

| Feature | Traditional LLM Agent | ROMA Framework |
|---------|----------------------|----------------|
| **Architecture** | Single monolithic agent | Hierarchical recursive decomposition |
| **Decision Process** | Direct prompt → action | Plan → decompose → execute → aggregate |
| **Complexity Handling** | Limited by prompt length | Recursively breaks down complex scenarios |
| **Parallelization** | Sequential execution | Can parallelize independent subtasks |
| **Transparency** | Black box reasoning | Clear task decomposition and reasoning chain |
| **Scalability** | Fixed complexity limit | Handles arbitrarily complex scenarios |
| **Error Recovery** | Single point of failure | Can re-plan at different levels |

**In Trading Context**: ROMA allows trading agents to:
- **Decompose complex market analysis** into parallelizable components (technical analysis, sentiment, risk assessment)
- **Aggregate multiple perspectives** before making final trading decisions
- **Maintain transparent reasoning** at each level of decision-making
- **Recover from errors** by re-planning at the appropriate abstraction level

---

## ✨ Features

- 🤖 **AI-Driven Trading**: Uses DSPy and large language models for intelligent decision-making
- 🔄 **Multi-Agent Architecture**: Run multiple trading strategies simultaneously
- ⚖️ **Advanced Risk Management**: 4-layer risk control system with position limits
- 🌐 **Multi-DEX Support**: Direct integration with Aster Finance DEX and Hyperliquid DEX
- 📊 **Monitoring Dashboard**: Next.js web interface for tracking agents and positions
- 📈 **Performance Tracking**: Comprehensive metrics and decision history
- 🔐 **Production Ready**: Secure, tested, and battle-hardened
- 📝 **Custom Prompts**: User-defined trading strategies
- 💬 **AI Chat Assistant**: Get real-time help with trading strategies, prompt suggestions, and platform features

### Frontend Status
- ✅ Agent overview and status monitoring
- ✅ Position tracking with real-time P/L
- ✅ Custom prompts for each agent
- ✅ Decision history and AI reasoning
- ✅ Performance metrics and charts
- ✅ AI Chat Assistant (new)
- ⚠️ WebSocket real-time updates (implemented, integration pending)
- 🔜 Advanced charting features (planned)
- 🔜 Strategy configuration UI (planned)

---

## 🚀 Quick Start

**Choose your deployment method:**
- 🐳 **Docker** (Recommended for production): See [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)
- 💻 **Local Development**: Follow the instructions below

### Prerequisites

- Python 3.12 or 3.13 (**NOT 3.14**)
- Node.js 18+
- API Keys (DeepSeek or other LLM provider)
- Aster DEX account with balance

### Installation (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/lukema95/roma-01.git
cd roma-01

# 2. Backend setup
cd backend
./setup.sh

# 3. Configure API keys
cp .env.example .env
nano .env  # Add your keys

# 4. Start backend
./start.sh

# 5. Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev
```

### Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

📖 **Full guide**: See [QUICKSTART.md](QUICKSTART.md)

---

## 📊 System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Next.js Frontend                    │
│  Dashboard │ Agent Detail │ Positions │ Performance    │
└────────────────────┬────────────────────────────────────┘
                     │ REST API + WebSocket
┌────────────────────┴────────────────────────────────────┐
│                  FastAPI Backend (Python)               │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   Agent    │  │   Trading    │  │  Decision      │ │
│  │  Manager   │→ │   Agent      │→ │  Logger        │ │
│  └────────────┘  └──────┬───────┘  └────────────────┘ │
│                         │                               │
│  ┌────────────────────┬┴─────────┬──────────────────┐ │
│  │  Aster DEX Toolkit │   DSPy   │  Technical       │ │
│  │  (Web3 API)        │  (AI)    │  Analysis        │ │
│  └────────────────────┴──────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Components

- **Agent Manager**: Orchestrates multiple AI trading agents with account-centric architecture
- **Trading Agent**: Makes decisions using DSPy + LLMs (DeepSeek, Qwen, Claude, Grok, Gemini, GPT)
- **DEX Toolkits**: 
  - **AsterToolkit**: Integrates with Aster Finance perpetual futures with EIP-191 signing
  - **HyperliquidToolkit**: Integrates with Hyperliquid DEX with native API support
- **Technical Analysis**: TA-Lib indicators (RSI, MACD, EMA, ATR, Bollinger Bands)
- **Risk Management**: Multi-layer position and capital protection (4-layer system)
- **Decision Logger**: Records all trades and AI reasoning in JSON format
- **Performance Analyzer**: Tracks metrics including win rate, Sharpe ratio, profit factor

---

## 🎯 Trading Flow

```
Every 3-5 minutes:

1. Scan Market
   ├─ Fetch prices, indicators, positions
   └─ Get account balance

2. AI Decision (DSPy)
   ├─ Analyze market conditions
   ├─ Evaluate risk/reward
   └─ Generate actions (open/close/hold)

3. Risk Validation
   ├─ Check single trade limits (50%/30%)
   ├─ Check total position limit (80%)
   └─ Validate minimum order sizes

4. Execute Trades
   ├─ Set leverage
   ├─ Place orders via Aster API
   └─ Record decision

5. Monitor & Log
   └─ Update dashboard and metrics
```

---

## 📚 Documentation

### Getting Started
- [Quick Start Guide](QUICKSTART.md) - Get up and running in 5 minutes
- [Configuration Guide](docs/CONFIGURATION.md) - Detailed configuration options

### Technical Documentation
- [Requirements](docs/REQUIREMENTS.md) - Project requirements and specifications  
- [Architecture](docs/ARCHITECTURE.md) - System design and implementation
- [Risk Management](docs/RISK_MANAGEMENT.md) - 4-layer risk control system

### Operations
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment  
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

📖 **Full documentation index**: [docs/README.md](docs/README.md)

---

## ⚙️ Configuration

### Account-Centric Architecture

ROMA-01 uses an **account-centric** configuration model where:
- **Accounts** define DEX trading accounts (Aster, Hyperliquid, etc.)
- **Models** define LLM configurations (DeepSeek, Qwen, Claude, etc.)
- **Agents** bind accounts with models to create trading agents

This allows flexible combinations: any account can use any model, and you can run multiple agents with different configurations.

```yaml
# config/trading_config.yaml

# Define DEX accounts
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

# Define LLM models
models:
  - id: "deepseek-v3.1"
    provider: "deepseek"
    api_key: ${DEEPSEEK_API_KEY}
    model: "deepseek-chat"
  
  - id: "qwen3-max"
    provider: "qwen"
    api_key: ${QWEN_API_KEY}
    model: "qwen-max"

# Create agents by binding accounts and models
agents:
  - id: "deepseek-aster-01"
    name: "DeepSeek on Aster-01"
    enabled: true
    account_id: "aster-acc-01"
    model_id: "deepseek-v3.1"
  
  - id: "qwen-hl-01"
    name: "Qwen on Hyperliquid-01"
    enabled: true
    account_id: "hl-acc-01"
    model_id: "qwen3-max"
```

**Benefits**:
- ✅ Mix and match accounts with models
- ✅ Run multiple agents on same DEX with different models
- ✅ Run multiple agents on different DEXs
- ✅ Each agent can have custom prompts and strategy

See [backend/config/README_CONFIG.md](backend/config/README_CONFIG.md) for detailed configuration guide.

### Trading Pairs

Each agent can trade the following perpetual futures:

```yaml
default_coins:
  - "BTCUSDT"     # Bitcoin
  - "ETHUSDT"     # Ethereum  
  - "SOLUSDT"     # Solana
  - "BNBUSDT"     # Binance Coin
  - "DOGEUSDT"    # Dogecoin
  - "XRPUSDT"     # Ripple
```

### Risk Management

Each model has customizable risk parameters:

```yaml
# Example: config/models/deepseek-chat-v3.1.yaml
risk_management:
  max_positions: 3              # Max concurrent positions
  max_leverage: 10              # Max leverage multiplier
  max_position_size_pct: 30     # Single position limit (% of account)
  max_total_position_pct: 80    # Total positions limit (% of account)
  max_single_trade_pct: 50      # Per-trade limit when no positions open
  max_single_trade_with_positions_pct: 30  # Per-trade limit with open positions
  max_daily_loss_pct: 15        # Daily loss circuit breaker
  stop_loss_pct: 3              # Automatic stop loss from entry
  take_profit_pct: 10           # Automatic take profit target
```

See [backend/config/README.md](backend/config/README.md) for detailed configuration guide.

### Supported DEXs

- **Aster Finance**: Perpetual futures with EIP-191 signing
  - Supports long/short positions
  - Leverage up to 10x
  - Multiple trading pairs (BTC, ETH, SOL, BNB, DOGE, XRP)

- **Hyperliquid**: Native DEX integration
  - Supports long/short positions
  - Leverage management
  - Multiple trading pairs (BTC, ETH, SOL, etc.)

### Supported LLMs

All models can be combined with any DEX account:

- **DeepSeek** (Recommended - fast & cheap, ~$0.14 per 1M tokens)
- **Qwen** - Good reasoning, multilingual
- **Claude** (Anthropic) - High quality, expensive
- **Grok** (xAI) - Real-time data access
- **Gemini** (Google) - Strong performance
- **GPT** (OpenAI) - Latest models

See [backend/config/README_CONFIG.md](backend/config/README_CONFIG.md) for complete configuration examples.

---

## 💰 Trading Features

### Supported
- ✅ Perpetual futures (long & short)
- ✅ **Aster Finance DEX** - Full integration with EIP-191 signing
- ✅ **Hyperliquid DEX** - Native API integration with leverage management
- ✅ **Account-Centric Architecture** - Flexible binding of accounts to models
- ✅ Multiple leverage options (1-10x)
- ✅ Technical indicators (RSI, MACD, BB)
- ✅ Auto position sizing
- ✅ Stop loss & take profit
- ✅ Multi-agent strategies
- ✅ Custom prompts per agent

### Coming Soon
- 🔜 Backtesting module
- 🔜 Strategy optimization
- 🔜 Mobile notifications

---

## 📡 Data Sources & Analysis

### Current Implementation
- ✅ **Technical Analysis**: K-line, RSI, MACD, EMA, ATR, Bollinger Bands, Volume

### Planned Enhancements
The platform is designed to integrate multiple information sources for comprehensive market analysis:

- 🔜 **News Sentiment**: Crypto news aggregation and sentiment scoring
- 🔜 **Social Intelligence**: Twitter/Reddit sentiment and Fear & Greed Index
- 🔜 **On-Chain Data**: Whale tracking, exchange flows, network metrics
- 🔜 **Macro Economics**: Fed policy, inflation data, market correlations
- 🔜 **Market Microstructure**: Order book depth, funding rates, liquidations

**ROMA Framework Advantage**: When multi-source analysis is implemented, ROMA's parallel execution architecture will enable simultaneous processing of all data sources, providing faster decisions with complete transparency and fault tolerance.

---

## 📈 Risk Management System

### 4-Layer Protection

1. **Single Trade Limits**
   - No positions: 50% max
   - With positions: 30% max

2. **Total Position Limit**
   - All positions: 80% max of balance

3. **Per-Position Limits**
   - Size: 30% max of account
   - Stop loss: 3% from entry
   - Take profit: 10% from entry

4. **Daily Limits**
   - Max daily loss: 15%

**Always keeps 20%+ reserve for safety**

---

## 🖥️ User Interface

Inspired by [NOF1.ai](https://nof1.ai/), this platform provides a competitive AI model showcase interface:

### Live Trading Dashboard
- **Multi-Agent Overview**: Monitor up to 6 different LLM models trading simultaneously
- **Real-time Performance**: Live account values, P/L tracking, and position updates
- **Price Ticker**: Real-time cryptocurrency prices for BTC, ETH, SOL, BNB, DOGE, XRP
- **Interactive Charts**: Visualize equity curves and performance comparisons across models

### Leaderboard View
- **Competitive Rankings**: Compare model performance with win rates, profit factors, and Sharpe ratios
- **Account Value Bars**: Visual representation of each model's trading account balance
- **Advanced Analytics**: Detailed metrics including completed trades, average hold time, and risk metrics
- **Model Status Indicators**: See which models are running and their current cycle counts

### Agent Detail View
- **Comprehensive Agent Information**: Full trading statistics and performance metrics
- **Current Positions**: Real-time position tracking with entry prices, current prices, and unrealized P/L
- **Decision History**: Complete AI reasoning logs showing how each trading decision was made
- **Performance Metrics**: Win rate, profit factor, Sharpe ratio, max drawdown, and more

### AI Chat Assistant
- **Interactive Chat Interface**: Chat directly with AI assistant from the right-side tabs
- **Trading Guidance**: Ask questions about trading strategies, prompt suggestions, and risk management
- **Platform Help**: Get assistance understanding platform features and capabilities
- **Real-time Responses**: Powered by the same LLM models used for trading decisions
- **Bilingual Support**: Full i18n support for English and Chinese

The interface design emphasizes transparency and comparison, allowing users to see how different AI models perform in identical market conditions.

_Screenshots coming soon_

---

## 🛡️ Security

- 🔐 API keys stored in environment variables
- 🔑 Private keys required for Web3 signatures
- 🔒 No keys committed to repository
- ⚠️ Always test on testnet first
- 💰 Start with small amounts

---

## 📊 Performance Metrics

Track your trading performance:

- **Total P/L**: Realized + unrealized profits
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline

All metrics available in real-time on the dashboard.

---

## 🔧 Tech Stack

### Backend
- Python 3.12/3.13
- FastAPI (REST API)
- DSPy (AI framework)
- Web3.py (DEX integration)
- TA-Lib (Technical analysis)
- httpx (Async HTTP)

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- SWR (Data fetching)
- Recharts (Charting)

### Infrastructure
- Docker / Docker Compose
- systemd / supervisor (Process management)
- Nginx (Reverse proxy)

---

## 📝 Project Structure

```
roma-01/
├── README.md              # This file
├── QUICKSTART.md          # Quick start guide
├── docs/                  # Documentation
│   ├── README.md          # Documentation index
│   ├── REQUIREMENTS.md    # Project requirements
│   ├── ARCHITECTURE.md    # System architecture
│   ├── CONFIGURATION.md   # Configuration guide
│   ├── RISK_MANAGEMENT.md # Risk management system
│   ├── DEPLOYMENT.md      # Deployment guide
│   └── TROUBLESHOOTING.md # Troubleshooting
├── backend/               # Python backend
│   ├── config/            # Configuration files
│   ├── src/               # Source code
│   │   └── roma_trading/
│   │       ├── agents/    # Trading agents
│   │       ├── api/       # REST API
│   │       ├── core/      # Core modules
│   │       └── toolkits/  # DEX & TA integrations
│   ├── logs/              # Trading logs
│   ├── setup.sh           # Setup script
│   └── start.sh           # Start script
└── frontend/              # Next.js frontend
    └── src/
        ├── app/           # Pages
        ├── components/    # React components
        └── lib/           # Utilities
```

---

## 🚦 Status

- ✅ **Backend**: Production ready
- ✅ **Frontend**: Production ready
- ✅ **Risk Management**: Fully implemented (4-layer system)
- ✅ **Aster DEX**: Integrated & tested
- ✅ **Hyperliquid DEX**: Integrated & tested
- ✅ **Account-Centric Architecture**: Flexible agent configuration
- ✅ **Technical Analysis**: RSI, MACD, BB, EMA, ATR
- ✅ **Multi-DEX Support**: Run agents on different DEXs simultaneously
- 🔜 **Multi-Source Analysis**: News, social, on-chain, macro data
- 🔜 **ROMA Integration**: Full hierarchical decision architecture
- 🔜 **Backtesting**: Strategy testing and optimization

---

## ⚠️ Disclaimer

This is an automated trading bot that executes real trades with real money.

- **No guarantees** of profitability
- **Past performance** does not predict future results
- **Test thoroughly** on testnet before using real funds
- **Start small** and monitor constantly
- **You may lose** your entire investment
- **Not financial advice** - for educational purposes only

**Trade at your own risk.**

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- 📖 Documentation: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/lukema95/roma-01/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/lukema95/roma-01/discussions)
- 📧 Email: lukema95@gmail.com

---

## 🙏 Acknowledgments

- **ROMA Framework**: For the hierarchical multi-agent architecture - see [ROMA documentation](../ROMA/README.md)
- **NOF1.ai**: For inspiration on competitive AI model showcase interface design
- **DSPy**: For structured AI prompting and agent orchestration
- **Aster Finance**: For the DEX integration and Web3 trading infrastructure
- **DeepSeek**: For fast and affordable LLM API

---

**Built with ❤️ using ROMA, DSPy, and AI**

**Last Updated**: 2025-11-06  
**Version**: 1.3.0  
**Status**: Production Ready ✅

