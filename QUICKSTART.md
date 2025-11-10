# ROMA-01 Quick Start Guide

## 🎯 Goal

Get ROMA-01 Trading Platform running in 5 minutes.

## 📋 Prerequisites

Before starting, make sure you have:

1. **Python 3.12 or 3.13** installed (⚠️ NOT 3.14 - DSPy doesn't support it yet)
2. **Node.js 18+** installed
3. **Aster DEX API Wallet** credentials:
   - Main wallet address (User)
   - API wallet address (Signer)
   - API wallet private key
   - Get them at: https://www.asterdex.com/en/api-wallet
4. **DeepSeek API Key** (recommended):
   - Sign up at: https://platform.deepseek.com
   - Cost: ~$0.14 per 1M tokens (very cheap!)

## 🚀 Step-by-Step Setup

### Step 1: Setup Backend Environment

**Option A: Automatic Setup (Recommended) 🚀**

```bash
cd /path/to/roma-01/backend
./setup.sh
```

The script will automatically:
- Detect the correct Python version (3.12 or 3.13)
- Create virtual environment
- Install all dependencies

**Option B: Manual Setup**

```bash
# Navigate to the project directory
cd /path/to/roma-01/backend

# Check Python version (must be 3.12 or 3.13)
python3 --version

# If you have Python 3.14, use 3.13 instead:
python3.13 --version  # Should show Python 3.13.x

# Create virtual environment (use python3.13 if you have 3.14)
python3.13 -m venv venv
# OR if you have 3.12:
# python3.12 -m venv venv
# OR if python3 is already 3.12 or 3.13:
# python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install backend dependencies
pip install -e .
```

⚠️ **Important**: Always activate the virtual environment before running the backend!

### Step 2: Configure Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use any editor
```

Add your credentials:

```env
# Aster DEX
ASTER_USER=0x...           # Your main wallet address
ASTER_SIGNER=0x...         # API wallet address
ASTER_PRIVATE_KEY=...      # API wallet private key (without 0x)

# DeepSeek AI
DEEPSEEK_API_KEY=sk-...    # Your DeepSeek API key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
CORS_ORIGINS=http://localhost:3000
```

### Step 3: Configure Trading Strategy (Optional)

The default configuration is ready to use, but you can customize:

```bash
# Edit main agent configuration
nano config/models/deepseek-chat-v3.1.yaml
```

Key settings:
- `default_coins`: Trading pairs (BTC, ETH, SOL, BNB, DOGE, XRP)
- `max_positions`: Maximum number of simultaneous positions (default: 3)
- `max_leverage`: Maximum leverage to use (default: 10x)
- `max_position_size_pct`: Position size as % of account (default: 30%)
- `stop_loss_pct`: Stop loss percentage (default: 3%)
- `take_profit_pct`: Take profit percentage (default: 10%)

For detailed configuration options, see [backend/config/README.md](backend/config/README.md)

### Step 4: Start the Backend

**Option A: Using Start Script (Recommended) 🚀**

```bash
cd /path/to/roma-01/backend
./start.sh
```

**Option B: Manual Start**

```bash
# Make sure you're in the backend directory
cd /path/to/roma-01/backend

# Activate virtual environment (if not already activated)
source venv/bin/activate

# Start the server
python -m roma_trading.main
```

You should see:

```
🚀 Starting ROMA Trading Platform
API Server: http://0.0.0.0:8080
Initialized TradingAgent: deepseek_aggressive
All agents started successfully
```

**Keep this terminal open!**

### Step 5: Setup and Start Frontend

Open a **NEW terminal**:

```bash
# Navigate to frontend directory
cd /path/to/roma-01/frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local

# Start development server
npm run dev
```

You should see:

```
ready - started server on 0.0.0.0:3000
```

### Step 6: Access the Platform

Open your browser and visit:

**http://localhost:3000**

You should see:
- List of active AI trading agents
- Real-time account balances
- Performance metrics
- Click on any agent to see detailed info

## ✅ Verification Checklist

- [ ] Backend is running on port 8080
- [ ] Frontend is running on port 3000
- [ ] Can access http://localhost:3000
- [ ] See agent cards with "Running" status
- [ ] Account balance is showing

## 🎉 Success!

Your ROMA-01 Trading Platform is now running!

## 📊 What Happens Next?

1. **First Decision**: The AI will make its first trading decision in ~3 minutes
2. **Market Analysis**: It analyzes 6 trading pairs (BTC, ETH, SOL, BNB, DOGE, XRP) with technical indicators
3. **Decision Making**: Uses DSPy Chain-of-Thought reasoning with configurable LLM
4. **Trade Execution**: Automatically places orders on Aster DEX with EIP-191 signing
5. **Performance Tracking**: Records all trades and calculates detailed metrics
6. **Real-time Updates**: Dashboard shows live positions, P&L, and AI reasoning

## 🔍 Monitoring

### Backend Logs

Watch the backend terminal for:
- Market data fetching
- AI decision making
- Trade execution
- Performance updates

### Frontend Dashboard

- **Main Page**: Overview of all agents
- **Agent Detail**: Click any agent card for:
  - Current positions
  - Recent decisions (with reasoning)
  - Performance metrics
  - Trade history

## ⚠️ Important Notes

### Safety First

1. **Start with Small Amounts**: Test with $10-50 first
2. **Monitor Closely**: Check the system every 10-15 minutes initially
3. **Understand Decisions**: Review the AI's reasoning in decision logs
4. **Set Limits**: Use the risk management settings

### Common Issues

**ModuleNotFoundError: No module named 'roma_trading':**
```bash
# Make sure you activated the virtual environment!
cd /path/to/roma-01/backend
source venv/bin/activate
python -m roma_trading.main
```

**Python version error (DSPy not found):**
```bash
# Check Python version
python3 --version

# If 3.14, you need to use 3.13 or 3.12
python3.13 --version

# Recreate virtual environment with correct Python
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install -e .
```

**Backend won't start:**
```bash
# Check if port 8080 is already in use
lsof -i :8080

# If yes, kill the process or change port in .env
```

**Frontend can't connect:**
```bash
# Verify backend is running
curl http://localhost:8080/health

# Should return: {"status":"healthy"}
```

**No trades happening:**
- AI is being conservative (this is normal!)
- Check market conditions
- Review decision logs for reasoning
- The system waits for high-confidence opportunities

### Stopping the System

**Graceful shutdown:**

1. Frontend terminal: Press `Ctrl+C`
2. Backend terminal: Press `Ctrl+C` and wait for "Stopped trading agent..."

## 🔧 Customization

### Add More Models

The platform supports 6 different LLMs. Edit `backend/config/trading_config.yaml`:

```yaml
agents:
  - id: "deepseek-chat-v3.1"
    enabled: true
    config_file: "config/models/deepseek-chat-v3.1.yaml"
  
  - id: "qwen3-max"
    enabled: true  # Enable second model
    config_file: "config/models/qwen3-max.yaml"
  
  - id: "claude-sonnet-4.5"
    enabled: true  # Enable third model
    config_file: "config/models/claude-sonnet-4.5.yaml"
```

**Note**: Each model requires its own API key and dedicated Aster DEX account.
See [backend/ACCOUNT_SETUP.md](backend/ACCOUNT_SETUP.md) for multi-account setup.

### Change Trading Pairs

Edit agent config file to customize trading pairs:

```yaml
strategy:
  default_coins:
    - "BTCUSDT"     # Bitcoin
    - "ETHUSDT"     # Ethereum
    - "SOLUSDT"     # Solana
    - "BNBUSDT"     # Binance Coin
    - "DOGEUSDT"    # Dogecoin
    - "XRPUSDT"     # Ripple
```

**Available Pairs**: BTC, ETH, SOL, BNB, DOGE, XRP (all paired with USDT)

## 📚 Next Steps

- Read the full README.md for detailed documentation
- Check agent detail pages for performance analytics
- Review decision logs to understand AI reasoning
- Experiment with different risk parameters
- Try multiple models in competition mode

## 🆘 Need Help?

- Check logs in `backend/logs/`
- Review decision logs in `backend/logs/decisions/{agent_id}/`
- GitHub Issues: Report bugs or ask questions

## 🎓 Understanding the System

### Decision Cycle (every 3 minutes):

1. **Fetch Data**: Account, positions, market prices
2. **Technical Analysis**: MACD, RSI, EMA, volume
3. **AI Analysis**: DSPy Chain-of-Thought reasoning
4. **Risk Check**: Validate against risk rules
5. **Execute**: Place orders on Aster DEX
6. **Log**: Record decision and performance

### Performance Metrics:

- **Win Rate**: % of profitable trades
- **Sharpe Ratio**: Risk-adjusted returns (higher is better)
- **Profit Factor**: Total profit / Total loss (>1 is profitable)
- **Max Drawdown**: Largest peak-to-trough decline

---

**Happy Trading! 🚀**

Remember: This is an AI system, not a guarantee of profits. Always trade responsibly.

