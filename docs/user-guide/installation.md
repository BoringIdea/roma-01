# Installation Guide

Complete installation guide for ROMA-01 Trading Platform.

---

## 📋 Prerequisites

### Required Software

1. **Python 3.12 or 3.13**
   - ⚠️ **NOT Python 3.14** (DSPy compatibility issue)
   - Check version: `python3 --version`
   - Download: https://www.python.org/downloads/

2. **Node.js 18 or higher**
   - Check version: `node --version`
   - Download: https://nodejs.org/

3. **Git**
   - For cloning the repository
   - Check version: `git --version`

### Required Accounts & API Keys

1. **Aster DEX API Wallet**
   - Sign up: https://www.asterdex.com/
   - Create API wallet: https://www.asterdex.com/en/api-wallet
   - You need:
     - Main wallet address (User)
     - API wallet address (Signer)
     - API wallet private key
   - Minimum balance: $10-50 USDT recommended for testing

2. **LLM API Key** (at least one)
   - **DeepSeek** (Recommended - cheap & fast):
     - Sign up: https://platform.deepseek.com
     - Cost: ~$0.14 per 1M tokens
   - **Alternatives**: Qwen, Claude, Grok, Gemini, GPT
   - See [Configuration Guide](configuration.md#llm-providers) for all options

---

## 🚀 Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/lukema95/roma-01.git
cd roma-01
```

### 2. Backend Setup

#### Option A: Automatic Setup (Recommended ⭐)

```bash
cd backend
./setup.sh
```

The script will:
- Detect correct Python version (3.12 or 3.13)
- Create virtual environment
- Install all dependencies
- Set up directory structure

#### Option B: Manual Setup

```bash
cd backend

# Check Python version
python3 --version  # Must be 3.12 or 3.13

# If you have 3.14, specify 3.13 explicitly
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate  # On Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -e .
```

### 3. Configure Environment Variables

```bash
cd backend

# Copy example file
cp .env.example .env

# Edit with your editor
nano .env
# or
vim .env
# or
code .env  # VS Code
```

**Minimum Required Variables**:
```bash
# LLM API Key (at least one)
DEEPSEEK_API_KEY=sk-your-key-here

# Aster DEX Credentials (for DeepSeek agent)
ASTER_USER_DEEPSEEK=0x0000...
ASTER_SIGNER_DEEPSEEK=0x0000...
ASTER_PRIVATE_KEY_DEEPSEEK=your-private-key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
CORS_ORIGINS=http://localhost:3000
```

See `backend/.env.example` for all available options.

### 4. Start Backend

```bash
cd backend

# Using start script (Recommended)
./start.sh

# OR manually
source venv/bin/activate
python -m roma_trading.main
```

**Expected Output**:
```
============================================================
🚀 Starting ROMA-01 Trading Platform
============================================================
API Server: http://0.0.0.0:8080
CORS Origins: http://localhost:3000
============================================================
INFO: Started server process
INFO: Waiting for application startup.
Initialized TradingAgent: deepseek-chat-v3.1 (DEEPSEEK CHAT V3.1)
All agents started successfully
INFO: Application startup complete.
```

**Keep this terminal open!**

### 5. Frontend Setup

Open a **new terminal**:

```bash
cd frontend

# Install dependencies
npm install
# or
yarn install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local

# Start development server
npm run dev
```

**Expected Output**:
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### 6. Access the Platform

Open your browser:

**Frontend Dashboard**: http://localhost:3000  
**Backend API**: http://localhost:8080  
**API Documentation**: http://localhost:8080/docs

You should see:
- ✅ Agent cards with status
- ✅ Account balances
- ✅ Price ticker (BTC, ETH, SOL, BNB, DOGE, XRP)
- ✅ Performance metrics

---

## ✅ Verification

### Check Backend

```bash
# Health check
curl http://localhost:8080/health
# Expected: {"status":"healthy"}

# List agents
curl http://localhost:8080/api/agents
# Expected: JSON array with agent info
```

### Check Frontend

1. Visit http://localhost:3000
2. See agent cards (should show "RUNNING")
3. Check account balance (should display)
4. Click on an agent card (should load detail page)

### Checklist

- [ ] Backend running on port 8080
- [ ] Frontend running on port 3000
- [ ] Can access dashboard at http://localhost:3000
- [ ] Agent cards show "RUNNING" status
- [ ] Account balance displays correctly
- [ ] Price ticker shows current prices
- [ ] Can click through to agent detail page

---

## 🐛 Troubleshooting

### Python Version Issues

**Error**: `ModuleNotFoundError: No module named 'dspy'`

**Solution**: You're using Python 3.14
```bash
# Check version
python3 --version

# Use 3.13 instead
python3.13 -m venv venv
source venv/bin/activate
pip install -e .
```

### Module Not Found

**Error**: `ModuleNotFoundError: No module named 'roma_trading'`

**Solution**: Activate virtual environment
```bash
cd backend
source venv/bin/activate  # You must do this!
python -m roma_trading.main
```

### Port Already in Use

**Error**: `Address already in use: 8080`

**Solution**: Kill process or change port
```bash
# Find process
lsof -i :8080

# Kill process
kill -9 <PID>

# OR change port in .env
API_PORT=8001
```

### Frontend Can't Connect

**Error**: Network error when loading data

**Solution**: Verify backend is running
```bash
# Test backend
curl http://localhost:8080/health

# If fails, check backend terminal for errors
```

### No Trades Happening

**This is normal!**
- AI is conservative
- Waits for high-confidence opportunities
- Check decision logs to see reasoning
- May take 30-60 minutes for first trade

---

## 🔧 Optional: Docker Installation

If you prefer Docker:

```bash
# From project root
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

**Access**:
- Frontend: http://localhost:3000
- Backend: http://localhost:8080

---

## 📦 System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 2GB
- **Disk**: 5GB free space
- **Network**: Stable internet connection

### Recommended
- **CPU**: 4+ cores
- **RAM**: 4GB+
- **Disk**: 10GB+ (for logs)
- **Network**: Low latency connection to exchanges

---

## 🎯 Next Steps

After installation:

1. **Review Configuration** - [Configuration Guide](configuration.md)
2. **Learn Trading Basics** - [Trading Basics](trading-basics.md)
3. **Understand Risk Management** - [Risk Management](../development/risk-management.md)
4. **Monitor Performance** - Dashboard at http://localhost:3000
5. **Review Decisions** - Check `backend/logs/decisions/`

---

## 🆘 Need Help?

- 📖 [Troubleshooting Guide](troubleshooting.md)
- 🐛 [GitHub Issues](https://github.com/lukema95/roma-01/issues)
- 💬 [Discussions](https://github.com/lukema95/roma-01/discussions)
- 📧 Email: lukema95@github.com

---

## ⚠️ Important Notes

### Security
- Never commit `.env` file
- Keep private keys secure
- Use separate accounts for testing
- Start with small amounts ($10-50)

### Performance
- First decision takes ~3 minutes
- AI is intentionally conservative
- Not every cycle will result in trades
- Monitor logs to understand AI reasoning

### Resources
- CPU usage: Low to moderate
- RAM usage: ~500MB backend, ~200MB frontend
- Network: Periodic API calls (not bandwidth intensive)

---

**Installation Time**: 5-10 minutes  
**Difficulty**: Easy  
**Support**: Full documentation available

---

**Last Updated**: November 2, 2025  
**Version**: 1.1.0

