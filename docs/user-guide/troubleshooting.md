# Troubleshooting Guide

Common issues and solutions for the ROMA Trading Platform.

---

## 📋 Table of Contents

1. [Setup Issues](#setup-issues)
2. [Trading Errors](#trading-errors)
3. [API Issues](#api-issues)
4. [Performance Issues](#performance-issues)
5. [Configuration Issues](#configuration-issues)
6. [Known Issues & Fixes](#known-issues--fixes)

---

## 🔧 Setup Issues

### Module Not Found: 'roma_trading'

**Error**:Known Issues & Fixes
```
ModuleNotFoundError: No module named 'roma_trading'
```

**Cause**: Package not installed or wrong Python environment

**Solution**:
```bash
cd backend
# Create virtual environment
python3.13 -m venv venv  # or python3.12
source venv/bin/activate

# Install package
pip install -e .
```

### Python Version Issues

**Error**:
```
error: Python 3.14 not supported
```

**Cause**: DSPy 3.0.3 doesn't support Python 3.14+

**Solution**:
```bash
# Check Python version
python3 --version

# Use Python 3.12 or 3.13
python3.13 -m venv venv
# or
python3.12 -m venv venv
```

### Missing README.md

**Error**:
```
OSError: Readme file does not exist: README.md
```

**Cause**: `pyproject.toml` expects README in backend directory

**Solution**:
```bash
cd backend
# README.md should exist - if not, create it
touch README.md
pip install -e .
```

---

## 💰 Trading Errors

### Margin is Insufficient

**Error**:
```
HTTP error: 400 - {"code":-2019,"msg":"Margin is insufficient."}
```

**Common Causes**:

#### 1. Stale Open Orders Locking Margin

**Solution**: Orders are now automatically cancelled at start of each cycle

#### 2. Minimum Order Exceeds Balance

**Error Log**:
```
Quantity too small (0.000218), adjusting to minimum 0.001
Required: $11.15, Available: $7.98
```

**Cause**: Minimum 0.001 quantity for expensive coins (BTC)

**Solution**:
- Trade cheaper coins (ETH, SOL, BNB)
- Increase balance
- System now skips trades automatically

**Log**:
```
❌ Minimum order (0.001) requires $11.15 margin,
   but only $7.98 available. Cannot trade BTCUSDT.
```

#### 3. Multiple Agents Racing

**Cause**: Two agents try to use same balance simultaneously

**Solution**: Trading lock implemented (agents take turns)

**Log**:
```
🔒 deepseek_aggressive acquired trading lock
...
🔓 deepseek_aggressive released trading lock
```

### Position Side Mismatch

**Error**:
```
HTTP error: 400 - {"code":-4061,"msg":"Order's position side does not match user's setting."}
```

**Cause**: Account in Hedge Mode, code was using "BOTH" (one-way mode)

**Solution**: ✅ Fixed - Now uses "LONG"/"SHORT" for hedge mode

**Code Fix**:
```python
# Now correctly uses hedge mode
"positionSide": "LONG"   # for long positions
"positionSide": "SHORT"  # for short positions
```

### Quantity Less Than Zero

**Error**:
```
HTTP error: 400 - {"code":-4003,"msg":"Quantity less than zero."}
```

**Cause**: Incorrect quantity calculation formula

**Wrong**:
```python
quantity = position_size_usd / price / leverage  # ❌
```

**Fixed**:
```python
quantity = (position_size_usd * leverage) / price  # ✅
```

### Signature Verification Failed

**Error**:
```
HTTP error: 403 - {"code":-1022,"msg":"Signature verification failed"}
```

**Cause**: Incorrect EIP-191 signature generation

**Solution**: ✅ Fixed - Now uses correct signing method

**Correct Implementation**:
```python
keccak_hash = Web3.keccak(encoded)
signable_message = encode_defunct(hexstr=keccak_hash.hex())
signed_message = Account.sign_message(signable_message, private_key=self.account.key)
```

---

## 🔌 API Issues

### API Key Invalid

**Error**:
```
Invalid API key
```

**Solution**:
1. Check `.env` file exists
2. Verify key format (no extra spaces)
3. Ensure variable name matches config:
```yaml
api_key: "${DEEPSEEK_API_KEY}"  # Must match .env
```

### Connection Timeout

**Error**:
```
TimeoutException: Request timed out
```

**Solutions**:
1. Check internet connection
2. Verify Aster DEX is accessible
3. Check firewall settings
4. Retry after a moment

### Rate Limiting

**Error**:
```
HTTP 429: Too Many Requests
```

**Solution**:
- Increase scan interval:
```yaml
scan_interval_minutes: 5  # Instead of 3
```
- Reduce number of active agents

---

## 📊 Performance Issues

### Slow AI Decisions

**Symptom**: Decision cycles take >30 seconds

**Causes & Solutions**:

1. **High temperature**: Reduce creativity
```yaml
temperature: 0.1  # Lower = faster
```

2. **Long max_tokens**: Reduce response length
```yaml
max_tokens: 2000  # Instead of 4000
```

3. **Model choice**: Use faster model
```yaml
model: "deepseek-chat"  # Fast
# vs
model: "gpt-4"  # Slower but smarter
```

### High Memory Usage

**Symptom**: Backend consuming >2GB RAM

**Solutions**:
1. Reduce concurrent agents
2. Clear old log files
3. Reduce `max_tokens` in config

---

## ⚙️ Configuration Issues

### Agent Not Trading

**Symptom**: Agent starts but makes no trades

**Checklist**:
1. ✅ Agent enabled?
```yaml
enabled: true
```

2. ✅ Sufficient balance?
```
Available balance > Minimum order size
```

3. ✅ Risk limits reasonable?
```yaml
max_position_size_pct: 30  # Not too low
```

4. ✅ Check logs for errors:
```bash
tail -f backend/logs/roma_trading_*.log
```

### Configuration Not Applied

**Symptom**: Changes don't take effect

**Solution**: Restart backend
```bash
cd backend
# Stop: Ctrl+C
./start.sh
```

⚠️ No hot reload - must restart

---

## 🐛 Known Issues & Fixes


**Problem**: AI wouldn't trade with $5-10 balance due to "$5 minimum" guideline

**Solution**: ✅ Fixed - Removed artificial minimum, added coin-specific guidance

**Prompt Update**:
```
- NO minimum balance limit - trade with whatever is available
- For BTCUSDT at $110k: minimum ~$11 margin @ 10x leverage
- For ETHUSDT at $3.9k: minimum ~$0.4 margin @ 10x leverage
- Choose coins you can ACTUALLY afford
```

---

## 🔍 Debugging Tips

### Enable Debug Logging

```yaml
# trading_config.yaml
system:
  log_level: "DEBUG"
```

Restart backend to apply.

### Check Decision Logs

```bash
cd backend/logs/decisions/deepseek_aggressive
cat decision_*.json | jq .
```

### Monitor Real-Time

```bash
cd backend
tail -f logs/roma_trading_*.log
```

### Check Account State

Via API:
```bash
curl http://localhost:8080/agents
curl http://localhost:8080/agent/deepseek_aggressive/account
```

### Test Single Component

```python
# Test Aster connection
from roma_trading.toolkits import AsterToolkit

toolkit = AsterToolkit(user="...", signer="...", private_key="...")
balance = await toolkit.get_account_balance()
print(balance)
```

---

## 📊 Error Code Reference

### Aster DEX Error Codes

| Code | Message | Meaning | Solution |
|------|---------|---------|----------|
| -1022 | Signature verification failed | Invalid signature | Check private key |
| -2019 | Margin is insufficient | Not enough balance | Increase balance or reduce position |
| -4003 | Quantity less than zero | Negative quantity | Check calculation |
| -4061 | Position side does not match | Hedge mode mismatch | Use LONG/SHORT |
| -1121 | Invalid symbol | Coin not supported | Check symbol name |

---

## 🆘 Emergency Procedures

### Stop All Trading Immediately

```bash
cd backend
# Method 1: Ctrl+C in terminal

# Method 2: Kill process
pkill -f roma_trading

# Method 3: Via API
curl -X POST http://localhost:8080/stop-all-agents
```

### Close All Positions Manually

Via Aster DEX UI:
1. Go to https://app.asterdex.com
2. Connect wallet
3. Navigate to Positions
4. Close each position manually

### Check System Health

```bash
# Backend logs
tail -100 backend/logs/roma_trading_*.log

# Agent status
curl http://localhost:8080/agents | jq .

# Account balance
curl http://localhost:8080/agent/deepseek_aggressive/account | jq .
```

---

## 📞 Getting Help

### Check Documentation
1. [Configuration Guide](CONFIGURATION.md)
2. [Architecture Documentation](ARCHITECTURE.md)
3. [Risk Management](RISK_MANAGEMENT.md)

### Check Logs
```bash
# Main log
cat backend/logs/roma_trading_$(date +%Y-%m-%d).log

# Specific agent decisions
cat backend/logs/decisions/deepseek_aggressive/decision_*.json
```

### Common Solutions Summary

| Issue | Quick Fix |
|-------|-----------|
| Module not found | `pip install -e .` in venv |
| Margin insufficient | Trade cheaper coins or increase balance |
| Position side mismatch | ✅ Already fixed |
| Signature failed | Check private key in `.env` |
| Agent not trading | Check enabled, balance, and logs |
| High memory | Reduce agents or max_tokens |
| Slow decisions | Lower temperature and max_tokens |

---

## ✅ Resolved Issues (Historical)

These issues have been permanently fixed in the current version:

- 

**Version**: 1.0.0  
**Last Updated**: 2025-10-31

---

**If issue persists, check [GitHub Issues](https://github.com) or contact support.**

