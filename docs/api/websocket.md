# WebSocket API Reference

Real-time updates for ROMA-01 Trading Platform.

---

## 📋 Overview

WebSocket endpoints provide real-time streaming updates for:
- Account balance changes
- Position updates  
- New trading decisions
- Trade executions
- Agent status changes

---

## 🔌 WebSocket Endpoint

### WS `/ws/agents/{agent_id}`

Connect to a specific agent for real-time updates.

**Endpoint**: `ws://localhost:8080/ws/agents/{agent_id}`

**Path Parameters**:
- `agent_id`: Agent identifier (e.g., "deepseek-chat-v3.1")

---

## 📡 Message Types

### 1. Account Update

Sent when account balance changes.

```json
{
  "type": "account_update",
  "timestamp": "2025-11-02T10:30:00Z",
  "data": {
    "total_balance": 10050.25,
    "available_balance": 8525.00,
    "unrealized_pnl": 50.25,
    "used_percentage": 15.0
  }
}
```

**Triggers**:
- New trade executed
- Position closed
- Mark price changes affecting P&L

---

### 2. Position Update

Sent when positions change.

```json
{
  "type": "position_update",
  "timestamp": "2025-11-02T10:30:15Z",
  "data": [
    {
      "symbol": "BTCUSDT",
      "side": "long",
      "position_amt": 0.001,
      "entry_price": 68080.0,
      "mark_price": 68500.0,
      "unrealized_profit": 0.50,
      "pnl_percentage": 0.74,
      "leverage": 10
    }
  ]
}
```

**Triggers**:
- Position opened
- Position closed
- Mark price update

---

### 3. Decision Update

Sent when AI makes a new trading decision.

```json
{
  "type": "decision",
  "timestamp": "2025-11-02T10:30:00Z",
  "data": {
    "cycle": 123,
    "agent_id": "deepseek-chat-v3.1",
    "ai_reasoning": "BTC showing strong bullish momentum with RSI(7) at 75.3...",
    "decisions": [
      {
        "action": "open_long",
        "symbol": "BTCUSDT",
        "quantity": 0.001,
        "leverage": 10,
        "reason": "Breakout above resistance with volume confirmation"
      }
    ]
  }
}
```

**Triggers**:
- Every trading cycle (every 3 minutes)
- AI completes decision-making process

---

### 4. Trade Executed

Sent when a trade is successfully executed.

```json
{
  "type": "trade_executed",
  "timestamp": "2025-11-02T10:30:05Z",
  "data": {
    "order_id": "12345678",
    "symbol": "BTCUSDT",
    "side": "long",
    "quantity": 0.001,
    "price": 68450.0,
    "leverage": 10,
    "status": "filled"
  }
}
```

**Triggers**:
- Order filled on exchange
- Position opened/closed successfully

---

### 5. Agent Status Update

Sent when agent status changes.

```json
{
  "type": "agent_status",
  "timestamp": "2025-11-02T10:30:00Z",
  "data": {
    "agent_id": "deepseek-chat-v3.1",
    "is_running": true,
    "cycle_count": 124,
    "last_decision_time": "2025-11-02T10:30:00Z"
  }
}
```

**Triggers**:
- Agent starts/stops
- Cycle completes
- Error occurs

---

## 💻 Client Implementation

### JavaScript/TypeScript

```typescript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8080/ws/agents/deepseek-chat-v3.1');

// Handle connection open
ws.onopen = () => {
  console.log('✅ Connected to agent updates');
};

// Handle incoming messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'account_update':
      updateAccountDisplay(message.data);
      break;
    
    case 'position_update':
      updatePositionsTable(message.data);
      break;
    
    case 'decision':
      showNewDecision(message.data);
      break;
    
    case 'trade_executed':
      notifyTradeExecution(message.data);
      break;
    
    default:
      console.log('Unknown message type:', message.type);
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error('❌ WebSocket error:', error);
};

// Handle connection close
ws.onclose = (event) => {
  console.log('Connection closed:', event.code, event.reason);
  
  // Implement reconnection logic
  setTimeout(() => {
    console.log('Attempting to reconnect...');
    reconnect();
  }, 5000);
};

// Reconnection function
function reconnect() {
  const newWs = new WebSocket('ws://localhost:8080/ws/agents/deepseek-chat-v3.1');
  // ... setup handlers again
}
```

### Python

```python
import asyncio
import websockets
import json

async def connect_to_agent(agent_id: str):
    uri = f"ws://localhost:8080/ws/agents/{agent_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"✅ Connected to {agent_id}")
        
        async for message in websocket:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "account_update":
                handle_account_update(data["data"])
            elif message_type == "position_update":
                handle_position_update(data["data"])
            elif message_type == "decision":
                handle_decision(data["data"])
            elif message_type == "trade_executed":
                handle_trade(data["data"])

def handle_account_update(data):
    print(f"💰 Balance: ${data['total_balance']:.2f}")

def handle_position_update(data):
    for pos in data:
        print(f"📊 {pos['symbol']} {pos['side']}: {pos['unrealized_profit']:+.2f}")

# Run
asyncio.run(connect_to_agent("deepseek-chat-v3.1"))
```

---

## 🔄 Connection Management

### Best Practices

**1. Automatic Reconnection**
```javascript
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.reconnectInterval = 5000;
    this.maxReconnectAttempts = 10;
    this.reconnectAttempts = 0;
    this.connect();
  }
  
  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('Connected');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, this.reconnectInterval);
      }
    };
    
    this.ws.onmessage = (event) => {
      this.handleMessage(JSON.parse(event.data));
    };
  }
  
  handleMessage(message) {
    // Handle different message types
  }
}
```

**2. Heartbeat/Ping**
```javascript
// Send ping every 30 seconds to keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

**3. Clean Disconnection**
```javascript
// Proper cleanup
window.addEventListener('beforeunload', () => {
  if (ws) {
    ws.close(1000, 'Page unload');
  }
});
```

---

## 🐛 Troubleshooting

### Connection Refused
**Error**: `WebSocket connection to 'ws://localhost:8080/...' failed`

**Solutions**:
- Verify backend is running on port 8080
- Check firewall settings
- Ensure WebSocket upgrade is supported

### Frequent Disconnections
**Solutions**:
- Implement heartbeat/ping mechanism
- Check network stability
- Increase server timeout settings

### No Messages Received
**Solutions**:
- Verify agent ID is correct
- Check if agent is running
- Review backend logs for errors

---

## 📊 Message Frequency

| Message Type | Frequency | Notes |
|--------------|-----------|-------|
| account_update | On change | When balance changes |
| position_update | On change | When positions change |
| decision | Every 3 min | Each trading cycle |
| trade_executed | On trade | When orders fill |
| agent_status | On change | Status changes only |

---

## 🔒 Security Considerations

### Production Setup

**1. Use WSS (Secure WebSocket)**
```javascript
// Development
ws://localhost:8080/ws/...

// Production
wss://your-domain.com/ws/...
```

**2. Authentication** (Recommended)
```javascript
// Add authentication token
const ws = new WebSocket('wss://api.example.com/ws/agents/agent-id?token=YOUR_TOKEN');
```

**3. Rate Limiting**
- Limit connections per IP
- Limit message frequency
- Implement backpressure

---

## 🔗 See Also

- [REST API Reference](rest-api.md) - HTTP endpoints
- [API Examples](examples.md) - More usage examples
- [Troubleshooting](../user-guide/troubleshooting.md) - Common issues

---

**Last Updated**: November 2, 2025  
**Version**: 1.1.0

