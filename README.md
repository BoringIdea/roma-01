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
- 🎨 **Model Showcase**: Display up to 6 different LLM models (DeepSeek, Qwen, Claude, Grok, Gemini, GPT) running simultaneously
- 📈 **Live Trading Dashboard**: Monitor positions, completed trades, and AI decision-making processes

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
- 🌐 **Web3 Integration**: Direct integration with Aster Finance DEX
- 📊 **Monitoring Dashboard**: Next.js web interface for tracking agents and positions
- 📈 **Performance Tracking**: Comprehensive metrics and decision history
- 🔐 **Production Ready**: Secure, tested, and battle-hardened

### Frontend Status
- ✅ Agent overview and status monitoring
- ✅ Position tracking with real-time P/L
- ✅ Decision history and AI reasoning
- ✅ Performance metrics and charts
- ⚠️ WebSocket real-time updates (implemented, integration pending)
- 🔜 Advanced charting features (planned)
- 🔜 Strategy configuration UI (planned)

---

## 🚀 Quick Start

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
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

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

- **Agent Manager**: Orchestrates multiple AI trading agents with independent accounts
- **Trading Agent**: Makes decisions using DSPy + LLMs (DeepSeek, Qwen, Claude, Grok, Gemini, GPT)
- **DEX Toolkit**: Integrates with Aster Finance perpetual futures with EIP-191 signing
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

### Agents

Run one or multiple agents with different strategies. Each agent uses its own dedicated trading account:

```yaml
# config/trading_config.yaml
agents:
  - id: "deepseek-chat-v3.1"
    name: "DEEPSEEK CHAT V3.1"
    enabled: true
    config_file: "config/models/deepseek-chat-v3.1.yaml"
  
  - id: "qwen3-max"
    name: "QWEN3 MAX"
    enabled: false
    config_file: "config/models/qwen3-max.yaml"
  
  - id: "claude-sonnet-4.5"
    name: "CLAUDE SONNET 4.5"
    enabled: false
    config_file: "config/models/claude-sonnet-4.5.yaml"
  
  - id: "grok-4"
    name: "GROK 4"
    enabled: false
    config_file: "config/models/grok-4.yaml"
  
  - id: "gemini-2.5-pro"
    name: "GEMINI 2.5 PRO"
    enabled: false
    config_file: "config/models/gemini-2.5-pro.yaml"
  
  - id: "gpt-5"
    name: "GPT 5"
    enabled: false
    config_file: "config/models/gpt-5.yaml"
```

**Note**: Enable multiple agents to run them simultaneously for strategy comparison.

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

### Supported LLMs

Each model has its own configuration file and dedicated trading account:

- **DeepSeek** (Recommended - fast & cheap, ~$0.14 per 1M tokens)
  - Model: `deepseek-chat`
  - Config: `config/models/deepseek-chat-v3.1.yaml`

- **Qwen**
  - Model: `qwen-max`
  - Config: `config/models/qwen3-max.yaml`

- **Claude** (Anthropic)
  - Model: `claude-sonnet-4.5`
  - Config: `config/models/claude-sonnet-4.5.yaml`

- **Grok** (xAI)
  - Model: `grok-4`
  - Config: `config/models/grok-4.yaml`

- **Gemini** (Google)
  - Model: `gemini-2.5-pro`
  - Config: `config/models/gemini-2.5-pro.yaml`

- **GPT** (OpenAI)
  - Model: `gpt-5`
  - Config: `config/models/gpt-5.yaml`

---

## 💰 Trading Features

### Supported
- ✅ Perpetual futures (long & short)
- ✅ Aster Finance DEX
- ✅ Multiple leverage options (1-10x)
- ✅ Technical indicators (RSI, MACD, BB)
- ✅ Auto position sizing
- ✅ Stop loss & take profit
- ✅ Multi-agent strategies

### Coming Soon
- 🔜 Hyperliquid DEX support
- 🔜 Backtesting module
- 🔜 Strategy optimization
- 🔜 Mobile notifications

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
- ✅ **Risk Management**: Fully implemented
- ✅ **Aster DEX**: Integrated & tested
- 🔜 **Hyperliquid**: Coming soon
- 🔜 **Backtesting**: Coming soon

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

**Last Updated**: 2025-11-02  
**Version**: 1.1.0  
**Status**: Production Ready ✅

