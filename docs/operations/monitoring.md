# Monitoring Guide

How to monitor and maintain your ROMA-01 trading platform in production.

---

## 📋 Table of Contents

- [Dashboard Monitoring](#dashboard-monitoring)
- [Log Monitoring](#log-monitoring)
- [Health Checks](#health-checks)
- [Alerts & Notifications](#alerts--notifications)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)

---

## 📊 Dashboard Monitoring

### Web Dashboard

**URL**: http://localhost:3000 (or your production domain)

**Key Indicators**:

**1. Agent Status Cards**
- 🟢 **LIVE**: Agent is running normally
- ⚫ **OFF**: Agent is stopped
- 🔴 **ERROR**: Agent encountered an error

**2. Account Balance**
- Monitor for unexpected drops
- Check available vs total balance
- Watch unrealized P&L

**3. Open Positions**
- Count should be ≤ max_positions (default: 3)
- P&L should be within stop loss/take profit range
- No positions stuck at liquidation price

**4. Performance Metrics**
- Win rate should be >50% (after 20+ trades)
- Profit factor should be >1.0
- Sharpe ratio should be positive

### Real-Time Updates

**Using WebSocket**:
```javascript
const ws = new WebSocket('ws://your-domain.com/ws/agents/deepseek-chat-v3.1');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === 'account_update') {
    checkBalance(msg.data);
  }
  
  if (msg.type === 'decision') {
    logDecision(msg.data);
  }
};

function checkBalance(data) {
  if (data.total_balance < ALERT_THRESHOLD) {
    sendAlert('Low balance warning!');
  }
}
```

---

## 📝 Log Monitoring

### Log Files Location

```
backend/logs/
├── roma_trading_2025-11-02.log          # Main log (daily rotation)
└── decisions/
    ├── deepseek-chat-v3.1/
    │   ├── decision_20251102_100000_cycle123.json
    │   └── ...
    └── qwen3-max/
        └── ...
```

### Main Log Monitoring

**Watch logs in real-time**:
```bash
# Tail main log
tail -f backend/logs/roma_trading_$(date +%Y-%m-%d).log

# Filter for specific agent
tail -f backend/logs/roma_trading_*.log | grep "deepseek-chat-v3.1"

# Show only errors
tail -f backend/logs/roma_trading_*.log | grep "ERROR"

# Show only trades
tail -f backend/logs/roma_trading_*.log | grep "Opening\|Closing"
```

### Log Patterns to Watch

**Normal Activity**:
```
INFO: Starting cycle #123
INFO: BTCUSDT: $68,450.23
INFO: Decision: wait - No high-confidence setups
```

**Trading Activity**:
```
INFO: Opening LONG BTCUSDT: 0.001 @ 10x leverage
INFO: Order placed successfully: 12345678
INFO: Closing LONG SOLUSDT: realized P&L +$2.50
```

**Warning Signs** ⚠️:
```
WARNING: Failed to fetch market price (attempt 2/3)
WARNING: Insufficient margin for trade
WARNING: Daily loss limit approaching: -12%
```

**Critical Issues** 🚨:
```
ERROR: Failed to place order: Signature error
ERROR: Agent crashed: Exception in trading loop
CRITICAL: DAILY LOSS LIMIT REACHED: -15.2%
```

### Decision Log Analysis

**Check recent decisions**:
```bash
# View latest decision
cat backend/logs/decisions/deepseek-chat-v3.1/decision_*.json | tail -1 | jq '.'

# Count decisions by action
cat backend/logs/decisions/deepseek-chat-v3.1/*.json | jq '.decisions[].action' | sort | uniq -c
```

**Analyze decision quality**:
```python
import json
from pathlib import Path

def analyze_decisions(agent_id: str):
    decisions_dir = Path(f"backend/logs/decisions/{agent_id}")
    
    actions = {"open_long": 0, "open_short": 0, "close": 0, "wait": 0}
    
    for file in decisions_dir.glob("*.json"):
        with open(file) as f:
            data = json.load(f)
            for decision in data.get("decisions", []):
                action = decision.get("action", "wait")
                actions[action] = actions.get(action, 0) + 1
    
    total = sum(actions.values())
    print(f"Total decisions: {total}")
    for action, count in actions.items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {action}: {count} ({pct:.1f}%)")

analyze_decisions("deepseek-chat-v3.1")
```

---

## 🏥 Health Checks

### Automated Health Monitoring

**Health Check Endpoint**:
```bash
# Simple health check
curl http://localhost:8080/health
# Expected: {"status":"healthy"}

# With timeout
curl --max-time 5 http://localhost:8080/health || echo "Backend is down!"
```

**Monitoring Script** (`monitor.sh`):
```bash
#!/bin/bash

BACKEND_URL="http://localhost:8080"
FRONTEND_URL="http://localhost:3000"

# Check backend
if curl -s --max-time 5 "$BACKEND_URL/health" | grep -q "healthy"; then
    echo "✅ Backend: OK"
else
    echo "❌ Backend: DOWN"
    # Send alert
fi

# Check frontend
if curl -s --max-time 5 "$FRONTEND_URL" > /dev/null; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: DOWN"
fi

# Check agent status
AGENTS=$(curl -s "$BACKEND_URL/api/agents")
RUNNING=$(echo "$AGENTS" | jq '[.[] | select(.is_running == true)] | length')
echo "🤖 Running Agents: $RUNNING"
```

**Run every 5 minutes**:
```bash
# Add to crontab
crontab -e

# Add this line:
*/5 * * * * /path/to/monitor.sh >> /var/log/roma01-monitor.log 2>&1
```

### System Resource Monitoring

```bash
# CPU and Memory usage
ps aux | grep "python.*roma_trading" | head -1

# Disk usage
du -sh backend/logs/

# Network connections
netstat -an | grep :8080
```

---

## 🔔 Alerts & Notifications

### What to Alert On

**Critical (Immediate Action)**:
- Backend crash
- Daily loss limit reached
- Exchange API errors >5 in 10 minutes
- Balance drop >20% in 1 hour

**Warning (Check Soon)**:
- Win rate <40% (after 20+ trades)
- Position stuck at liquidation
- No decisions for >1 hour
- Disk space <1GB

**Info (Monitor)**:
- New trade executed
- Daily summary
- Performance milestones

### Alert Implementation

**Email Alerts** (using Python):
```python
import smtplib
from email.mime.text import MIMEText

def send_email_alert(subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = f"ROMA-01 Alert: {subject}"
    msg['From'] = "alerts@yourdomain.com"
    msg['To'] = "you@email.com"
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login("your-email", "your-password")
        server.send_message(msg)

# Usage
if daily_loss_pct < -10:
    send_email_alert(
        "High Loss Warning",
        f"Daily loss: {daily_loss_pct:.2f}%"
    )
```

**Telegram Alerts**:
```python
import requests

def send_telegram(message: str):
    BOT_TOKEN = "your-bot-token"
    CHAT_ID = "your-chat-id"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    
    requests.post(url, data=data)

# Usage
send_telegram(f"🚨 Daily loss limit reached: -15.2%")
```

---

## 📈 Performance Monitoring

### Daily Summary Script

```python
from datetime import datetime, timedelta

def daily_summary(agent_id: str):
    """Generate daily performance summary."""
    
    # Get performance
    perf = client.get(f"/api/agents/{agent_id}/performance")
    account = client.get(f"/api/agents/{agent_id}/account")
    
    # Get today's trades
    trades = client.get(f"/api/agents/{agent_id}/trades?limit=100")
    today = datetime.now().date()
    today_trades = [t for t in trades if datetime.fromtimestamp(t['time']/1000).date() == today]
    
    # Calculate daily P&L
    daily_pnl = sum(t.get('realized_pnl', 0) for t in today_trades)
    
    # Report
    report = f"""
📊 Daily Summary for {agent_id}
Date: {today}

💰 Account:
  Total Balance: ${account['total_balance']:.2f}
  P&L Today: ${daily_pnl:+.2f}
  Available: ${account['available_balance']:.2f}

📈 Performance:
  Total Trades: {len(today_trades)} today, {perf['total_trades']} total
  Win Rate: {perf['win_rate']:.1f}%
  Profit Factor: {perf['profit_factor']:.2f}
  Sharpe Ratio: {perf['sharpe_ratio']:.2f}

📊 Open Positions: {len(client.get(f'/api/agents/{agent_id}/positions'))}
    """
    
    print(report)
    return report

# Run at end of each day
summary = daily_summary("deepseek-chat-v3.1")
# Send via email/Telegram
```

### Long-term Tracking

**Track equity curve**:
```python
import matplotlib.pyplot as plt
from datetime import datetime

def plot_equity_curve(agent_id: str):
    equity = client.get(f"/api/agents/{agent_id}/equity-history?limit=1000")
    
    timestamps = [datetime.fromisoformat(e['timestamp']) for e in equity]
    values = [e['equity'] for e in equity]
    
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, values)
    plt.title(f'Equity Curve - {agent_id}')
    plt.xlabel('Time')
    plt.ylabel('Account Value ($)')
    plt.grid(True)
    plt.savefig(f'equity_{agent_id}.png')
    
plot_equity_curve("deepseek-chat-v3.1")
```

---

## 🔧 Maintenance Tasks

### Daily
- [  ] Check agent status (all running?)
- [  ] Review daily P&L
- [  ] Check for errors in logs
- [  ] Verify exchange connectivity

### Weekly
- [  ] Review performance metrics
- [  ] Analyze decision quality
- [  ] Check disk space
- [  ] Backup decision logs
- [  ] Update API keys if needed

### Monthly
- [  ] Review overall strategy performance
- [  ] Adjust risk parameters if needed
- [  ] Update dependencies
- [  ] Review and archive old logs
- [  ] Disaster recovery test

### Log Rotation

Logs are automatically rotated daily. To manage old logs:

```bash
# Keep last 7 days (default)
# Configure in backend/src/roma_trading/main.py:
# retention="7 days"

# Manual cleanup (keep last 30 days)
find backend/logs/ -name "*.log" -mtime +30 -delete
```

---

## 🚨 Emergency Procedures

### Agent Not Responding

```bash
# 1. Check if process is running
ps aux | grep "roma_trading"

# 2. Check logs for errors
tail -100 backend/logs/roma_trading_*.log

# 3. Restart
cd backend
./start.sh
```

### High Losses

```bash
# 1. Stop agent immediately
# Press Ctrl+C in backend terminal

# 2. Review recent decisions
cat backend/logs/decisions/*/decision_*.json | tail -5 | jq '.decisions'

# 3. Check positions
curl http://localhost:8080/api/agents/deepseek-chat-v3.1/positions

# 4. Close positions manually if needed (via Aster DEX)

# 5. Adjust risk parameters before restarting
nano backend/config/models/deepseek-chat-v3.1.yaml
# Reduce: max_leverage, max_position_size_pct
```

### Exchange API Issues

```bash
# 1. Test connectivity
curl https://fapi.asterdex.com/fapi/v3/ping

# 2. Check API status
curl https://fapi.asterdex.com/fapi/v3/time

# 3. If down, agent will retry automatically
# Check logs for retry attempts

# 4. If persistent, stop agent and wait for exchange recovery
```

---

## 📊 Monitoring Tools

### Recommended Tools

**1. Uptime Monitoring**:
- [UptimeRobot](https://uptimerobot.com/) - Free tier available
- Monitor: http://your-domain.com/health

**2. Log Management**:
- [Papertrail](https://papertrailapp.com/) - Centralized logging
- [Logtail](https://logtail.com/) - Log aggregation

**3. Application Performance**:
- [New Relic](https://newrelic.com/) - APM
- [Datadog](https://www.datadoghq.com/) - Infrastructure monitoring

**4. Custom Dashboard**:
- [Grafana](https://grafana.com/) - Visualization
- [Prometheus](https://prometheus.io/) - Metrics collection

### Simple Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 📈 Key Metrics to Track

### Application Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| API Response Time | <200ms | >500ms |
| Trading Cycle Duration | <30s | >60s |
| Error Rate | <1% | >5% |
| Memory Usage | <500MB | >1GB |
| CPU Usage | <50% | >80% |

### Trading Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| Win Rate | >55% | <40% (after 20 trades) |
| Profit Factor | >1.5 | <1.0 |
| Sharpe Ratio | >1.0 | <0.5 |
| Max Drawdown | <10% | >15% |
| Daily Loss | <5% | >10% |

### System Metrics

| Metric | Target | Alert If |
|--------|--------|----------|
| Disk Space | >5GB free | <1GB |
| Log Files | <1GB/day | >5GB/day |
| Open Connections | <10 | >50 |
| Agent Uptime | >99% | <95% |

---

## 🔍 Diagnostic Commands

### Check Agent Health

```bash
#!/bin/bash
# health-check.sh

AGENT_ID="deepseek-chat-v3.1"

echo "🔍 Agent Health Check"
echo "===================="

# Get agent status
STATUS=$(curl -s http://localhost:8080/api/agents/$AGENT_ID | jq -r '.is_running')
echo "Status: $STATUS"

# Get cycle count
CYCLES=$(curl -s http://localhost:8080/api/agents/$AGENT_ID | jq -r '.cycle_count')
echo "Cycles: $CYCLES"

# Get account
BALANCE=$(curl -s http://localhost:8080/api/agents/$AGENT_ID/account | jq -r '.total_balance')
echo "Balance: \$$BALANCE"

# Get positions
POSITIONS=$(curl -s http://localhost:8080/api/agents/$AGENT_ID/positions | jq 'length')
echo "Open Positions: $POSITIONS"

# Check recent errors
ERRORS=$(tail -100 backend/logs/roma_trading_*.log | grep ERROR | wc -l)
echo "Recent Errors: $ERRORS"

if [ "$ERRORS" -gt 5 ]; then
    echo "⚠️  WARNING: High error count!"
fi
```

### Performance Check

```bash
# Quick performance snapshot
curl -s http://localhost:8080/api/agents/deepseek-chat-v3.1/performance | jq '{
  win_rate,
  total_pnl,
  profit_factor,
  sharpe_ratio,
  total_trades
}'
```

---

## 🛡️ Backup & Recovery

### What to Backup

**Critical**:
- `backend/.env` - Credentials
- `backend/config/` - Configuration files
- `backend/logs/decisions/` - Decision history

**Optional**:
- `backend/logs/*.log` - Main logs (large files)
- Database file - If using persistent storage

### Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/roma01_$DATE"

mkdir -p "$BACKUP_DIR"

# Backup config
cp -r backend/config "$BACKUP_DIR/"

# Backup decisions (last 30 days)
find backend/logs/decisions -mtime -30 -name "*.json" | cpio -pdm "$BACKUP_DIR/"

# Backup .env (encrypted!)
gpg -c backend/.env -o "$BACKUP_DIR/env.gpg"

# Compress
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "✅ Backup created: ${BACKUP_DIR}.tar.gz"
```

**Run weekly**:
```bash
# Add to crontab
0 2 * * 0 /path/to/backup.sh
```

---

## 📞 Support & Escalation

### Issue Severity Levels

**P0 - Critical** (Fix immediately):
- Backend completely down
- All trades failing
- Daily loss >15%
- Data loss

**P1 - High** (Fix within hours):
- Single agent down
- Intermittent API errors
- Performance degradation
- Daily loss >10%

**P2 - Medium** (Fix within days):
- Individual feature not working
- Documentation issues
- UI bugs
- Win rate declining

**P3 - Low** (Nice to have):
- Feature requests
- Optimization opportunities
- Documentation improvements

### Getting Help

1. Check [Troubleshooting Guide](../user-guide/troubleshooting.md)
2. Search [GitHub Issues](https://github.com/lukema95/roma-01/issues)
3. Ask in [Discussions](https://github.com/lukema95/roma-01/discussions)
4. Contact: lukema95@github.com

---

## 🔗 See Also

- [Deployment Guide](deployment.md) - Production setup
- [Troubleshooting](../user-guide/troubleshooting.md) - Common issues
- [API Reference](../api/rest-api.md) - Programmatic monitoring

---

**Last Updated**: November 2, 2025  
**Version**: 1.1.0

