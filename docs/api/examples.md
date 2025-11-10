# API Usage Examples

Practical examples of using the ROMA-01 API in different programming languages.

---

## 📋 Table of Contents

- [Python Examples](#python-examples)
- [JavaScript/TypeScript Examples](#javascripttypescript-examples)
- [cURL Examples](#curl-examples)
- [Common Use Cases](#common-use-cases)

---

## Python Examples

### Basic Setup

```python
import requests
import json

BASE_URL = "http://localhost:8080"

class RomaClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
    
    def get(self, endpoint: str):
        response = requests.get(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()

client = RomaClient()
```

### Get All Agents

```python
# Get list of agents
agents = client.get("/api/agents")

for agent in agents:
    print(f"Agent: {agent['name']}")
    print(f"  Status: {'🟢 Running' if agent['is_running'] else '⚫ Stopped'}")
    print(f"  Cycles: {agent['cycle_count']}")
    print()
```

### Monitor Agent Performance

```python
def monitor_agent(agent_id: str):
    # Get account
    account = client.get(f"/api/agents/{agent_id}/account")
    print(f"💰 Balance: ${account['total_balance']:.2f}")
    print(f"   Available: ${account['available_balance']:.2f}")
    print(f"   P&L: ${account['unrealized_pnl']:+.2f}")
    
    # Get positions
    positions = client.get(f"/api/agents/{agent_id}/positions")
    print(f"\n📊 Open Positions: {len(positions)}")
    for pos in positions:
        pnl_emoji = "🟢" if pos['unrealized_profit'] > 0 else "🔴"
        print(f"   {pnl_emoji} {pos['symbol']} {pos['side'].upper()}")
        print(f"      Entry: ${pos['entry_price']:.2f}")
        print(f"      Current: ${pos['mark_price']:.2f}")
        print(f"      P&L: ${pos['unrealized_profit']:+.2f} ({pos['pnl_percentage']:+.2f}%)")
    
    # Get performance
    perf = client.get(f"/api/agents/{agent_id}/performance")
    print(f"\n📈 Performance:")
    print(f"   Win Rate: {perf['win_rate']:.1f}%")
    print(f"   Total P&L: ${perf['total_pnl']:+.2f}")
    print(f"   Profit Factor: {perf['profit_factor']:.2f}")
    print(f"   Sharpe Ratio: {perf['sharpe_ratio']:.2f}")

# Usage
monitor_agent("deepseek-chat-v3.1")
```

### Stream Real-Time Updates

```python
import asyncio
import websockets
import json

async def stream_agent_updates(agent_id: str):
    uri = f"ws://localhost:8080/ws/agents/{agent_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"✅ Connected to {agent_id}\n")
        
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            timestamp = data.get("timestamp", "")
            
            if msg_type == "account_update":
                balance = data["data"]["total_balance"]
                pnl = data["data"]["unrealized_pnl"]
                print(f"[{timestamp}] 💰 Balance: ${balance:.2f} | P&L: ${pnl:+.2f}")
            
            elif msg_type == "decision":
                cycle = data["data"]["cycle"]
                decisions = data["data"]["decisions"]
                print(f"[{timestamp}] 🤖 Cycle #{cycle}: {len(decisions)} decisions")
                for d in decisions:
                    print(f"   → {d['action']} {d.get('symbol', 'N/A')}")
            
            elif msg_type == "trade_executed":
                trade = data["data"]
                print(f"[{timestamp}] ✅ Trade: {trade['side']} {trade['symbol']} @ ${trade['price']}")

# Run
asyncio.run(stream_agent_updates("deepseek-chat-v3.1"))
```

---

## JavaScript/TypeScript Examples

### Fetch API (REST)

```typescript
const BASE_URL = "http://localhost:8080";

interface Agent {
  id: string;
  name: string;
  is_running: boolean;
  cycle_count: number;
}

// Get all agents
async function getAllAgents(): Promise<Agent[]> {
  const response = await fetch(`${BASE_URL}/api/agents`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json();
}

// Get agent performance
async function getPerformance(agentId: string) {
  const response = await fetch(`${BASE_URL}/api/agents/${agentId}/performance`);
  return await response.json();
}

// Usage
const agents = await getAllAgents();
console.log(`Found ${agents.length} agents`);

for (const agent of agents) {
  if (agent.is_running) {
    const perf = await getPerformance(agent.id);
    console.log(`${agent.name}: Win Rate ${perf.win_rate}%`);
  }
}
```

### WebSocket (Real-time)

```typescript
interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: any;
}

class AgentMonitor {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  constructor(private agentId: string) {
    this.connect();
  }
  
  private connect() {
    this.ws = new WebSocket(`ws://localhost:8080/ws/agents/${this.agentId}`);
    
    this.ws.onopen = () => {
      console.log('✅ Connected');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('Connection closed');
      this.attemptReconnect();
    };
  }
  
  private handleMessage(message: WebSocketMessage) {
    switch (message.type) {
      case 'account_update':
        this.onAccountUpdate?.(message.data);
        break;
      case 'position_update':
        this.onPositionUpdate?.(message.data);
        break;
      case 'decision':
        this.onDecision?.(message.data);
        break;
    }
  }
  
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), 5000);
    }
  }
  
  // Event handlers (set these from outside)
  onAccountUpdate?: (data: any) => void;
  onPositionUpdate?: (data: any) => void;
  onDecision?: (data: any) => void;
  
  disconnect() {
    this.ws?.close();
  }
}

// Usage
const monitor = new AgentMonitor('deepseek-chat-v3.1');

monitor.onAccountUpdate = (data) => {
  console.log(`Balance: $${data.total_balance}`);
};

monitor.onDecision = (data) => {
  console.log(`New decision (cycle ${data.cycle}):`, data.decisions);
};
```

### React Hook

```typescript
import { useEffect, useState } from 'react';

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  reconnect?: boolean;
}

export function useAgentWebSocket(agentId: string, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8080/ws/agents/${agentId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
      options.onMessage?.(message);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
    };
    
    return () => {
      ws.close();
    };
  }, [agentId]);
  
  return { isConnected, lastMessage };
}

// Usage in component
function AgentDashboard({ agentId }: { agentId: string }) {
  const { isConnected, lastMessage } = useAgentWebSocket(agentId, {
    onMessage: (msg) => {
      if (msg.type === 'trade_executed') {
        showNotification('Trade executed!');
      }
    }
  });
  
  return (
    <div>
      <div>Status: {isConnected ? '🟢 Connected' : '⚫ Disconnected'}</div>
      {/* Render data... */}
    </div>
  );
}
```

---

## cURL Examples

### Get Agents
```bash
curl http://localhost:8080/api/agents
```

### Get Agent Account
```bash
curl http://localhost:8080/api/agents/deepseek-chat-v3.1/account
```

### Get Positions (Pretty Print)
```bash
curl http://localhost:8080/api/agents/deepseek-chat-v3.1/positions | jq '.'
```

### Get Market Prices
```bash
curl "http://localhost:8080/api/market/prices?symbols=BTCUSDT,ETHUSDT"
```

### Get Recent Decisions
```bash
curl "http://localhost:8080/api/agents/deepseek-chat-v3.1/decisions?limit=5" | jq '.[] | {cycle, decisions}'
```

### WebSocket (with wscat)
```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8080/ws/agents/deepseek-chat-v3.1
```

---

## Common Use Cases

### 1. Build a Custom Dashboard

```typescript
import useSWR from 'swr';

export function CustomDashboard() {
  // Poll REST API every 30 seconds
  const { data: agents } = useSWR('/api/agents', {
    refreshInterval: 30000
  });
  
  // Use WebSocket for real-time updates
  const { lastMessage } = useAgentWebSocket('deepseek-chat-v3.1');
  
  // Combine data
  return (
    <div>
      {agents?.map(agent => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
      {lastMessage && <LiveUpdate message={lastMessage} />}
    </div>
  );
}
```

### 2. Alert on Large Trades

```python
async def trade_alerter(agent_id: str, min_value_usd: float = 100):
    uri = f"ws://localhost:8080/ws/agents/{agent_id}"
    
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            
            if data["type"] == "trade_executed":
                trade = data["data"]
                value = trade["quantity"] * trade["price"]
                
                if value >= min_value_usd:
                    send_alert(
                        title=f"Large Trade Alert",
                        message=f"{trade['side']} {trade['symbol']}: ${value:.2f}"
                    )

def send_alert(title: str, message: str):
    # Send to Telegram, email, etc.
    print(f"🚨 {title}: {message}")
```

### 3. Performance Tracker

```python
import time
from datetime import datetime

def track_performance_over_time(agent_id: str, interval_minutes: int = 30):
    """Track and log performance metrics over time."""
    
    while True:
        # Get current performance
        perf = client.get(f"/api/agents/{agent_id}/performance")
        account = client.get(f"/api/agents/{agent_id}/account")
        
        # Log to file
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "balance": account["total_balance"],
            "pnl": perf["total_pnl"],
            "win_rate": perf["win_rate"],
            "sharpe_ratio": perf["sharpe_ratio"]
        }
        
        print(f"[{timestamp}] Balance: ${account['total_balance']:.2f} | "
              f"Win Rate: {perf['win_rate']:.1f}% | "
              f"Sharpe: {perf['sharpe_ratio']:.2f}")
        
        # Save to CSV
        with open(f"performance_{agent_id}.csv", "a") as f:
            f.write(f"{timestamp},{log_entry['balance']},{log_entry['pnl']},"
                   f"{log_entry['win_rate']},{log_entry['sharpe_ratio']}\n")
        
        # Wait for next interval
        time.sleep(interval_minutes * 60)
```

### 4. Multi-Agent Comparison

```python
async def compare_agents():
    """Compare performance across all agents."""
    
    agents = client.get("/api/agents")
    
    results = []
    for agent in agents:
        if agent["is_running"]:
            perf = client.get(f"/api/agents/{agent['id']}/performance")
            account = client.get(f"/api/agents/{agent['id']}/account")
            
            results.append({
                "name": agent["name"],
                "balance": account["total_balance"],
                "pnl": perf["total_pnl"],
                "win_rate": perf["win_rate"],
                "sharpe": perf["sharpe_ratio"],
                "trades": perf["total_trades"]
            })
    
    # Sort by P&L
    results.sort(key=lambda x: x["pnl"], reverse=True)
    
    # Display
    print("\n📊 Agent Performance Comparison\n")
    print(f"{'Agent':<25} {'Balance':>10} {'P&L':>10} {'Win%':>6} {'Sharpe':>7} {'Trades':>7}")
    print("="*80)
    
    for r in results:
        print(f"{r['name']:<25} ${r['balance']:>9.2f} ${r['pnl']:>9.2f} "
              f"{r['win_rate']:>5.1f}% {r['sharpe']:>6.2f} {r['trades']:>7}")
```

---

## JavaScript/TypeScript Examples

### Using Fetch API

```javascript
const BASE_URL = "http://localhost:8080";

// Get agents with error handling
async function getAgents() {
  try {
    const response = await fetch(`${BASE_URL}/api/agents`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch agents:', error);
    return [];
  }
}

// Get market prices
async function getMarketPrices(symbols = ["BTCUSDT", "ETHUSDT"]) {
  const params = new URLSearchParams({ symbols: symbols.join(",") });
  const response = await fetch(`${BASE_URL}/api/market/prices?${params}`);
  return await response.json();
}
```

### React Component with SWR

```typescript
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(r => r.json());

export function AgentCard({ agentId }: { agentId: string }) {
  // Auto-refresh every 30 seconds
  const { data: account, error } = useSWR(
    `/api/agents/${agentId}/account`,
    fetcher,
    { refreshInterval: 30000 }
  );
  
  const { data: positions } = useSWR(
    `/api/agents/${agentId}/positions`,
    fetcher,
    { refreshInterval: 30000 }
  );
  
  if (error) return <div>Error loading data</div>;
  if (!account) return <div>Loading...</div>;
  
  return (
    <div>
      <h2>{agentId}</h2>
      <p>Balance: ${account.total_balance.toFixed(2)}</p>
      <p>P&L: ${account.unrealized_pnl.toFixed(2)}</p>
      <p>Open Positions: {positions?.length || 0}</p>
    </div>
  );
}
```

### WebSocket with Auto-Reconnect

```javascript
class RomaWebSocket {
  constructor(agentId) {
    this.agentId = agentId;
    this.url = `ws://localhost:8080/ws/agents/${agentId}`;
    this.reconnectDelay = 5000;
    this.maxReconnectAttempts = 10;
    this.reconnectCount = 0;
    this.handlers = {};
    
    this.connect();
  }
  
  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log(`✅ Connected to ${this.agentId}`);
      this.reconnectCount = 0;
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const handler = this.handlers[message.type];
      if (handler) {
        handler(message.data);
      }
    };
    
    this.ws.onclose = () => {
      console.log('Connection closed');
      this.attemptReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  attemptReconnect() {
    if (this.reconnectCount < this.maxReconnectAttempts) {
      this.reconnectCount++;
      console.log(`Reconnecting... (${this.reconnectCount}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connect(), this.reconnectDelay);
    } else {
      console.error('Max reconnect attempts reached');
    }
  }
  
  on(messageType, handler) {
    this.handlers[messageType] = handler;
    return this;
  }
  
  disconnect() {
    this.ws?.close();
  }
}

// Usage
const monitor = new RomaWebSocket('deepseek-chat-v3.1');

monitor
  .on('account_update', (data) => {
    console.log('Balance:', data.total_balance);
  })
  .on('decision', (data) => {
    console.log('New decision:', data.decisions);
  })
  .on('trade_executed', (data) => {
    alert(`Trade executed: ${data.symbol} ${data.side}`);
  });
```

---

## cURL Examples

### Basic Queries

```bash
# Get API info
curl http://localhost:8080/

# Health check
curl http://localhost:8080/health

# List agents
curl http://localhost:8080/api/agents | jq '.'

# Get specific agent
curl http://localhost:8080/api/agents/deepseek-chat-v3.1 | jq '.'
```

### Account & Positions

```bash
# Get account balance
curl http://localhost:8080/api/agents/deepseek-chat-v3.1/account | jq '.total_balance'

# Get positions
curl http://localhost:8080/api/agents/deepseek-chat-v3.1/positions | jq '.[] | {symbol, side, pnl: .unrealized_profit}'

# Get performance
curl http://localhost:8080/api/agents/deepseek-chat-v3.1/performance | jq '{win_rate, total_pnl, sharpe_ratio}'
```

### Decisions & Trades

```bash
# Get recent decisions (last 5)
curl "http://localhost:8080/api/agents/deepseek-chat-v3.1/decisions?limit=5" | jq '.[] | {cycle, action: .decisions[0].action}'

# Get trade history
curl "http://localhost:8080/api/agents/deepseek-chat-v3.1/trades?limit=10" | jq '.[] | {symbol, side, pnl: .realized_pnl}'
```

### Market Data

```bash
# Get all default prices
curl http://localhost:8080/api/market/prices | jq '.[] | {symbol, price}'

# Get specific symbols
curl "http://localhost:8080/api/market/prices?symbols=BTCUSDT,ETHUSDT" | jq '.'
```

### Monitoring Script

```bash
#!/bin/bash
# monitor-agent.sh - Quick agent monitoring

AGENT_ID="deepseek-chat-v3.1"
BASE_URL="http://localhost:8080"

echo "📊 ROMA-01 Agent Monitor"
echo "Agent: $AGENT_ID"
echo "========================"

# Account
echo "💰 Account:"
curl -s "$BASE_URL/api/agents/$AGENT_ID/account" | jq '{balance: .total_balance, available: .available_balance, pnl: .unrealized_pnl}'

# Positions
echo -e "\n📈 Positions:"
curl -s "$BASE_URL/api/agents/$AGENT_ID/positions" | jq '.[] | {symbol, side, pnl: .unrealized_profit}'

# Performance
echo -e "\n📊 Performance:"
curl -s "$BASE_URL/api/agents/$AGENT_ID/performance" | jq '{win_rate, total_pnl, sharpe_ratio}'
```

---

## 🎯 Common Patterns

### Polling vs WebSocket

**Use REST API + Polling when**:
- Updates don't need to be instant
- Simpler implementation preferred
- Client is stateless

```javascript
// Poll every 30 seconds
setInterval(async () => {
  const data = await fetch('/api/agents/deepseek-chat-v3.1/account');
  updateUI(await data.json());
}, 30000);
```

**Use WebSocket when**:
- Need instant updates
- High frequency of changes
- Building real-time dashboard

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/agents/deepseek-chat-v3.1');
ws.onmessage = (event) => {
  updateUI(JSON.parse(event.data));
};
```

### Error Handling Best Practices

```typescript
async function safeApiFetch<T>(endpoint: string): Promise<T | null> {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`);
    
    if (!response.ok) {
      const error = await response.json();
      console.error('API Error:', error.detail);
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('Network Error:', error);
    return null;
  }
}

// Usage
const account = await safeApiFetch<Account>('/api/agents/deepseek-chat-v3.1/account');
if (account) {
  console.log('Balance:', account.total_balance);
} else {
  console.log('Failed to fetch account data');
}
```

---

## 🔗 See Also

- [REST API Reference](rest-api.md) - Complete endpoint documentation
- [WebSocket Reference](websocket.md) - WebSocket details
- [User Guide](../user-guide/configuration.md) - Configuration options

---

**Last Updated**: November 2, 2025  
**Version**: 1.1.0

