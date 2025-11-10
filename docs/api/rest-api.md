# REST API Reference

Complete reference for ROMA-01 REST API endpoints.

---

## 📋 Base Information

**Base URL**: `http://localhost:8080`  
**Version**: 1.1.0  
**Authentication**: None (add in production)

For production deployment, implement:
- API key authentication
- JWT tokens
- IP whitelisting
- Rate limiting

---

## 📡 API Endpoints

### System Endpoints

#### GET `/`
Get API root information.

**Response**:
```json
{
  "name": "ROMA-01 Trading API",
  "version": "1.1.0",
  "status": "running"
}
```

#### GET `/health`
Health check endpoint for monitoring.

**Response**:
```json
{
  "status": "healthy"
}
```

---

### Agent Endpoints

#### GET `/api/agents`
Get list of all trading agents.

**Response**:
```json
[
  {
    "id": "deepseek-chat-v3.1",
    "name": "DEEPSEEK CHAT V3.1",
    "is_running": true,
    "cycle_count": 42,
    "runtime_minutes": 126
  }
]
```

**cURL Example**:
```bash
curl http://localhost:8080/api/agents
```

---

#### GET `/api/agents/{agent_id}`
Get detailed information about a specific agent.

**Path Parameters**:
- `agent_id` (string): Agent identifier (e.g., "deepseek-chat-v3.1")

**Response**:
```json
{
  "id": "deepseek-chat-v3.1",
  "name": "DEEPSEEK CHAT V3.1",
  "is_running": true,
  "cycle_count": 42,
  "runtime_minutes": 126,
  "last_decision_time": "2025-11-02T20:00:00Z",
  "config": {
    "model": "deepseek-chat",
    "provider": "deepseek",
    "scan_interval_minutes": 3,
    "max_leverage": 10,
    "default_coins": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"]
  }
}
```

**Error Responses**:
```json
{
  "detail": "Agent not found: invalid_id"
}
```

---

#### GET `/api/agents/{agent_id}/account`
Get account balance information for an agent.

**Response**:
```json
{
  "total_balance": 10050.25,
  "available_balance": 8500.00,
  "unrealized_pnl": 50.25,
  "total_positions_value": 1500.00,
  "used_percentage": 15.0
}
```

**Fields**:
- `total_balance`: Total account value (wallet + unrealized P&L)
- `available_balance`: Available capital for new trades
- `unrealized_pnl`: Unrealized profit/loss from open positions
- `total_positions_value`: Sum of all position values
- `used_percentage`: Percentage of account in use

---

#### GET `/api/agents/{agent_id}/positions`
Get current open positions for an agent.

**Response**:
```json
[
  {
    "symbol": "BTCUSDT",
    "side": "long",
    "position_amt": 0.001,
    "entry_price": 68080.0,
    "mark_price": 68500.0,
    "unrealized_profit": 0.50,
    "pnl_percentage": 0.74,
    "leverage": 10,
    "liquidation_price": 61200.0,
    "margin_type": "cross"
  }
]
```

**Empty Response** (no positions):
```json
[]
```

---

#### GET `/api/agents/{agent_id}/performance`
Get performance metrics for an agent.

**Response**:
```json
{
  "total_trades": 25,
  "winning_trades": 15,
  "losing_trades": 10,
  "win_rate": 60.0,
  "total_pnl": 125.50,
  "gross_profit": 200.00,
  "gross_loss": -74.50,
  "profit_factor": 2.68,
  "sharpe_ratio": 1.85,
  "max_drawdown": -15.25,
  "max_drawdown_pct": -1.52,
  "avg_win": 13.33,
  "avg_loss": -7.45,
  "largest_win": 45.00,
  "largest_loss": -18.50,
  "current_streak": 3
}
```

**Metrics Explained**:
- `win_rate`: Percentage of profitable trades
- `profit_factor`: Gross profit / Absolute gross loss (>1 is profitable)
- `sharpe_ratio`: Risk-adjusted returns (>1 is good, >2 is excellent)
- `current_streak`: Positive = winning streak, negative = losing streak

---

#### GET `/api/agents/{agent_id}/analytics`
Get detailed trading analytics.

**Response**:
```json
{
  "performance": {...},
  "trade_distribution": {
    "by_symbol": {...},
    "by_hour": {...},
    "by_day_of_week": {...}
  },
  "risk_metrics": {
    "avg_leverage": 8.5,
    "max_position_size": 25.0,
    "avg_hold_time_minutes": 180
  }
}
```

---

#### GET `/api/agents/{agent_id}/decisions`
Get decision history with AI reasoning.

**Query Parameters**:
- `limit` (integer, optional): Number of decisions to return (default: 10, max: 100)

**Response**:
```json
[
  {
    "timestamp": "2025-11-02T10:30:00Z",
    "cycle": 123,
    "ai_reasoning": "Market shows bullish signals...",
    "decisions": [
      {
        "action": "open_long",
        "symbol": "BTCUSDT",
        "quantity": 0.001,
        "leverage": 10,
        "reason": "Strong uptrend with RSI oversold bounce"
      }
    ],
    "execution_results": [
      {
        "success": true,
        "order_id": "12345",
        "message": "Order placed successfully"
      }
    ]
  }
]
```

---

#### GET `/api/agents/{agent_id}/equity-history`
Get historical equity curve data.

**Query Parameters**:
- `limit` (integer, optional): Number of data points (default: 100)

**Response**:
```json
[
  {
    "timestamp": "2025-11-02T10:00:00Z",
    "equity": 10000.00
  },
  {
    "timestamp": "2025-11-02T10:30:00Z",
    "equity": 10025.50
  }
]
```

**Use Case**: Plot equity curve chart on frontend

---

#### GET `/api/agents/{agent_id}/trades`
Get trade history.

**Query Parameters**:
- `limit` (integer, optional): Number of trades to return (default: 50, max: 500)

**Response**:
```json
[
  {
    "id": "123456",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "position_side": "LONG",
    "price": 68080.0,
    "quantity": 0.001,
    "realized_pnl": 2.50,
    "commission": 0.05,
    "time": 1699012808000
  }
]
```

---

### Market Endpoints

#### GET `/api/market/prices`
Get current market prices for trading pairs.

**Query Parameters**:
- `symbols` (string, optional): Comma-separated symbols (e.g., "BTCUSDT,ETHUSDT")

**Response**:
```json
[
  {
    "symbol": "BTCUSDT",
    "price": 68450.25
  },
  {
    "symbol": "ETHUSDT",
    "price": 3892.60
  }
]
```

**Default Symbols** (if not specified):
- BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, DOGEUSDT, XRPUSDT

---

## ⚠️ Error Handling

### Standard Error Response
```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource not found (e.g., agent not found) |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Exchange API unavailable |

### Common Errors

#### Agent Not Found (404)
```json
{
  "detail": "Agent not found: invalid_id"
}
```
**Solution**: Check available agents with `GET /api/agents`

#### Service Error (500/503)
```json
{
  "detail": "Failed to fetch account balance: Connection timeout"
}
```
**Solution**: 
- Check if backend is running
- Verify exchange API connectivity
- Check logs for details

---

## 🔄 Rate Limiting

**Current**: No rate limiting implemented

**Production Recommendations**:
- Implement rate limiting (e.g., 100 requests/minute per IP)
- Use caching for frequently accessed data
- Add retry logic with exponential backoff

---

## 📚 Interactive API Documentation

When the backend is running, visit:

**Swagger UI**: http://localhost:8080/docs  
**ReDoc**: http://localhost:8080/redoc

These provide:
- Interactive API testing
- Automatic request/response examples
- Schema documentation

---

## 🔗 See Also

- [WebSocket API](websocket.md) - Real-time updates
- [API Examples](examples.md) - Usage examples in different languages
- [Deployment Guide](../operations/deployment.md) - Production setup

---

**Last Updated**: November 2, 2025  
**Version**: 1.1.0

