# ROMA AI Trading Platform - Architecture Design Document

## 📋 Document Information

| Item | Content |
|------|---------|
| **Project Name** | ROMA AI Crypto Futures Trading Platform |
| **Version** | v1.1.0 |
| **Date** | November 2, 2025 |
| **Status** | Production |
| **Tech Stack** | ROMA + Python 3.12+ + Aster Finance API v3 + Next.js 14 |

---

## 📑 Table of Contents

- [1. System Architecture](#1-system-architecture)
- [2. Core Modules](#2-core-modules)
- [3. Data Models](#3-data-models)
- [4. API Integration](#4-api-integration)
- [5. Security Design](#5-security-design)
- [6. Performance Optimization](#6-performance-optimization)
- [7. Deployment](#7-deployment)

---

## 1. System Architecture

### 1.1 Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│  ┌────────────┬────────────┬────────────┬──────────────────┐    │
│  │ Next.js UI │ REST API   │ WebSocket  │ API Docs (Swagger)│    │
│  └────────────┴────────────┴────────────┴──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Backend Layer (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     Agent Manager                         │   │
│  │      (Orchestrates multiple AI trading agents)            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                  Trading Agent (x6)                     │     │
│  │  ┌──────────┬───────────┬──────────┬─────────────┐     │     │
│  │  │ DSPy AI  │ Decision  │ Risk     │ Performance │     │     │
│  │  │ Module   │ Logger    │ Manager  │ Analyzer    │     │     │
│  │  └──────────┴───────────┴──────────┴─────────────┘     │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Toolkit Layer                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            BaseDEXToolkit (Abstract Interface)            │   │
│  │  • Unified interface for all DEX integrations            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌──────────────────────┬──────────────────────┐              │
│  │   AsterToolkit       │  HyperliquidToolkit   │              │
│  │  • EIP-191 Signing   │  • Native API        │              │
│  │  • Aster Finance API  │  • Leverage Mgmt     │              │
│  │  • Trading & Data     │  • Trading & Data    │              │
│  └──────────────────────┴──────────────────────┘              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           TechnicalAnalysisToolkit (TA-Lib)              │   │
│  │  • RSI, MACD, EMA, ATR                                   │   │
│  │  • Bollinger Bands                                       │   │
│  │  • Volume Analysis                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   External Services                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  DEX Services                              │   │
│  │  • Aster Finance API v3 (fapi.asterdex.com)              │   │
│  │  • Hyperliquid API (api.hyperliquid.xyz)                 │   │
│  │  • Perpetual Futures Trading                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                LLM Services                               │   │
│  │  • DeepSeek, Qwen, Claude, Grok, Gemini, GPT            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

#### Backend
```python
# Core Framework
FastAPI 0.104+              # REST API framework
Python 3.12/3.13           # Programming language
Uvicorn                    # ASGI server

# AI & Decision Making
DSPy 2.4+                  # AI framework
LiteLLM                    # Unified LLM interface

# Trading & Analysis
Web3.py                    # Blockchain integration
eth-account                # EIP-191 signing
hyperliquid-python-sdk     # Hyperliquid DEX integration
TA-Lib                     # Technical indicators
httpx                      # Async HTTP client

# Utilities
Pydantic                   # Data validation
Loguru                     # Logging
asyncio                    # Async operations
```

#### Frontend
```javascript
// Framework
Next.js 14                 // React framework
TypeScript                 // Type safety
React 18                   // UI library

// Styling
Tailwind CSS               // Utility-first CSS
PostCSS                    // CSS processing

// Data & State
SWR                        // Data fetching
Zustand                    // State management

// Visualization
Recharts                   // Charting library
date-fns                   // Date utilities
```

### 1.3 Project Structure

```
roma-01/
├── backend/
│   ├── config/
│   │   ├── README.md                    # Configuration guide
│   │   ├── README_CONFIG.md             # Account-centric config guide
│   │   ├── QUICK_START.md               # Quick start guide
│   │   └── trading_config.yaml          # Main config (account-centric)
│   ├── src/
│   │   └── roma_trading/
│   │       ├── __init__.py
│   │       ├── main.py                  # Entry point
│   │       ├── agents/
│   │       │   ├── __init__.py
│   │       │   ├── agent_manager.py     # Agent orchestration
│   │       │   └── trading_agent.py     # Core trading logic
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   └── main.py              # FastAPI app
│   │       ├── config/
│   │       │   ├── __init__.py
│   │       │   └── settings.py          # Settings management
│   │       ├── core/
│   │       │   ├── __init__.py
│   │       │   ├── analytics.py         # Trading analytics
│   │       │   ├── decision_logger.py   # Decision logging
│   │       │   └── performance.py       # Performance metrics
│   │       └── toolkits/
│   │           ├── __init__.py
│   │           ├── base_dex.py          # DEX interface
│   │           ├── aster_toolkit.py     # Aster DEX impl
│   │           └── technical_analysis.py # TA indicators
│   ├── logs/                            # Trading logs
│   ├── setup.sh                         # Setup script
│   ├── start.sh                         # Start script
│   └── pyproject.toml                   # Dependencies
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx               # Root layout
    │   │   ├── page.tsx                 # Home page
    │   │   ├── agent/[id]/page.tsx      # Agent detail
    │   │   ├── leaderboard/page.tsx     # Leaderboard
    │   │   └── models/page.tsx          # Models page
    │   ├── components/
    │   │   ├── agent/                   # Agent components
    │   │   ├── chart/                   # Chart components
    │   │   ├── layout/                  # Layout components
    │   │   └── leaderboard/             # Leaderboard components
    │   ├── lib/
    │   │   ├── api.ts                   # API client
    │   │   ├── model/                   # Model utilities
    │   │   └── utils/                   # Utility functions
    │   ├── store/                       # State management
    │   └── types/                       # TypeScript types
    ├── public/                          # Static assets
    ├── package.json                     # Dependencies
    └── next.config.js                   # Next.js config
```

---

## 2. Core Modules

### 2.1 Agent Manager

**File**: `backend/src/roma_trading/agents/agent_manager.py`

**Responsibilities**:
- Load agent configurations from YAML files
- Initialize and start multiple trading agents
- Coordinate trading lock across agents
- Provide agent status information
- Graceful shutdown handling

**Key Methods**:
```python
class AgentManager:
    async def load_agents_from_config() -> None
        """Load agents from trading_config.yaml"""
    
    async def start_all() -> None
        """Start all enabled agents"""
    
    async def stop_all() -> None
        """Stop all running agents"""
    
    def get_agent(agent_id: str) -> TradingAgent
        """Get agent by ID"""
    
    def get_all_agents() -> List[Dict]
        """Get all agent statuses"""
```

**Configuration Flow**:
```
trading_config.yaml
    ↓
Load enabled agents
    ↓
For each agent:
    Read model config (e.g., deepseek-chat-v3.1.yaml)
    ↓
    Initialize TradingAgent(id, config, trading_lock)
    ↓
    Start agent loop
```

### 2.2 Trading Agent

**File**: `backend/src/roma_trading/agents/trading_agent.py`

**Core Components**:

```python
class TradingAgent:
    def __init__(agent_id, config, trading_lock):
        """
        Initialize agent with:
        - DEX toolkit (AsterToolkit)
        - Technical analysis (TechnicalAnalysisToolkit)
        - Decision logger (DecisionLogger)
        - Performance analyzer (PerformanceAnalyzer)
        - DSPy LLM module
        """
    
    async def trading_loop():
        """
        Main trading cycle (every 3-5 minutes):
        1. Fetch market data and positions
        2. Calculate technical indicators
        3. Get AI decision via DSPy
        4. Validate with risk management
        5. Execute trades
        6. Log decision and update metrics
        """
    
    def _init_llm():
        """Initialize LLM based on provider (DeepSeek, Qwen, etc.)"""
    
    async def _make_decision() -> Dict:
        """
        Use DSPy Chain-of-Thought to generate decision:
        - Input: System prompt + market context
        - Output: Reasoning + JSON decisions
        """
    
    async def _execute_decisions(decisions: List[Dict]):
        """Execute validated trading decisions"""
```

**Trading Cycle**:
```
Every scan_interval_minutes (default: 3):

1. Acquire trading_lock (prevent concurrent trades)
   ↓
2. Fetch Data
   - Account balance
   - Current positions
   - Market prices for all coins
   - Historical klines (100 candles)
   ↓
3. Calculate Technical Indicators
   - RSI (7-period and 14-period)
   - MACD
   - EMA (20-period)
   - ATR
   ↓
4. Build Market Context
   - Format data as string
   - Include account status
   - Include position info
   - Include performance metrics
   ↓
5. AI Decision Making (DSPy)
   - Chain-of-Thought reasoning
   - Generate JSON decisions
   - Parse and validate output
   ↓
6. Risk Management Validation
   - Check single trade limits
   - Check total position limits
   - Check minimum order sizes
   - Validate available balance
   ↓
7. Execute Trades
   - Close positions (if decided)
   - Open long positions
   - Open short positions
   ↓
8. Log & Update
   - Save decision log (JSON)
   - Update performance metrics
   - Release trading_lock
```

### 2.3 DSPy Integration

**AI Decision Signature**:
```python
class TradingDecision(dspy.Signature):
    """
    AI Trading Decision Signature
    """
    # Inputs
    system_prompt: str = dspy.InputField(
        desc="Trading rules and constraints"
    )
    market_context: str = dspy.InputField(
        desc="Current market state, account, positions, performance"
    )
    
    # Outputs
    chain_of_thought: str = dspy.OutputField(
        desc="Reasoning process and analysis"
    )
    decisions_json: str = dspy.OutputField(
        desc="JSON array of trading decisions"
    )
```

**Decision Module**:
```python
# Initialize DSPy Chain-of-Thought
decision_module = dspy.ChainOfThought(TradingDecision)

# Make decision
result = decision_module(
    system_prompt=system_rules,
    market_context=market_data
)

# Parse output
reasoning = result.chain_of_thought
decisions = json.loads(result.decisions_json)
```

**System Prompt Structure**:
```
You are a professional crypto futures trader on Aster DEX.

ACCOUNT STATUS:
- Balance: $X.XX USDT
- Available: $Y.YY USDT
- Positions: [list]
- Performance: [metrics]

MARKET DATA:
- [For each coin]
  Symbol: BTCUSDT
  Price: $X.XX
  1h Change: +X.XX%
  4h Change: +X.XX%
  RSI(7): XX.X
  RSI(14): XX.X
  MACD: XX.XX
  Signal: XX.XX
  Histogram: XX.XX
  EMA20: $X.XX
  Volume: XXX

TRADING RULES:
1. Risk Management: [limits]
2. Position Sizing: [rules]
3. Stop Loss/Take Profit: [levels]
4. Strategy: [guidelines]

OUTPUT FORMAT:
{
  "decisions": [
    {
      "action": "open_long" | "open_short" | "close" | "wait",
      "symbol": "BTCUSDT",
      "quantity": 0.001,
      "leverage": 10,
      "side": "long" | "short",
      "reason": "explanation"
    }
  ]
}
```

### 2.4 Risk Management System

**4-Layer Protection**:

```python
# Layer 1: Single Trade Limits
def check_single_trade_limit(amount: float) -> bool:
    """
    Limit new trade size based on existing positions
    - No positions: max 50% of available
    - With positions: max 30% of available
    """
    has_positions = len(current_positions) > 0
    limit_pct = 0.30 if has_positions else 0.50
    max_trade = available_balance * limit_pct
    return amount <= max_trade

# Layer 2: Total Position Limit
def check_total_position_limit(new_trade: float) -> bool:
    """
    Ensure total exposure doesn't exceed 80% of balance
    - Sum all position values
    - Add new trade value
    - Check against 80% limit
    """
    total_used = sum(pos["value"] for pos in positions)
    total_used += new_trade
    return total_used <= (total_balance * 0.80)

# Layer 3: Per-Position Limits
def check_position_limits(symbol: str, size: float) -> bool:
    """
    Individual position constraints:
    - Max position size: 30% of account
    - Max leverage: 10x
    - Stop loss: 3% from entry
    - Take profit: 10% from entry
    """
    position_value = size * price
    return position_value <= (total_balance * 0.30)

# Layer 4: Daily Loss Limit
def check_daily_loss() -> bool:
    """
    Circuit breaker for excessive daily losses
    - Track daily P&L
    - Stop trading if loss > 15% of starting balance
    """
    daily_loss_pct = (daily_pnl / starting_balance) * 100
    return daily_loss_pct > -15.0
```

**Minimum Order Validation**:
```python
def validate_minimum_order(symbol: str, quantity: float) -> bool:
    """
    Ensure order meets exchange minimums
    - Get minimum quantity from exchange info
    - Check if quantity >= minimum
    - Account for precision and step size
    """
    precision = await get_precision(symbol)
    min_qty = precision["min_quantity"]
    return quantity >= min_qty
```

### 2.5 Aster DEX Toolkit

**File**: `backend/src/roma_trading/toolkits/aster_toolkit.py`

**Core Features**:
- EIP-191 signature authentication
- Automatic precision handling
- Network retry logic
- Position management

**Key Methods**:

```python
class AsterToolkit(BaseDEXToolkit):
    
    async def get_account_balance() -> Dict:
        """
        Fetch account balance
        Returns: {
            "total_wallet_balance": float,
            "available_balance": float,
            "total_unrealized_profit": float
        }
        """
    
    async def get_positions() -> List[Dict]:
        """
        Get current open positions
        Returns: [{
            "symbol": str,
            "side": "long" | "short",
            "position_amt": float,
            "entry_price": float,
            "mark_price": float,
            "unrealized_profit": float,
            "leverage": int,
            "liquidation_price": float
        }]
        """
    
    async def get_market_price(symbol: str) -> float:
        """Get current market price for symbol"""
    
    async def get_klines(symbol: str, interval: str, limit: int) -> List[Dict]:
        """
        Get historical kline/candlestick data
        Returns: [{
            "open_time": int,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float,
            "close_time": int
        }]
        """
    
    async def open_long(symbol: str, quantity: float, leverage: int) -> Dict:
        """
        Open long position
        1. Cancel existing orders
        2. Set leverage
        3. Get precision
        4. Place limit order (1% above market)
        """
    
    async def open_short(symbol: str, quantity: float, leverage: int) -> Dict:
        """
        Open short position
        1. Cancel existing orders
        2. Set leverage
        3. Get precision
        4. Place limit order (1% below market)
        """
    
    async def close_position(symbol: str, side: str) -> Dict:
        """
        Close existing position
        1. Get current position
        2. Calculate close quantity
        3. Place opposite order
        4. Cancel remaining orders
        """
    
    async def get_user_trades(
        symbol: Optional[str],
        start_time: Optional[int],
        end_time: Optional[int],
        limit: int
    ) -> List[Dict]:
        """
        Get trade history
        - Query by symbol or all symbols
        - Time range filtering
        - Includes realized P&L
        """
```

**EIP-191 Signing Process**:
```python
async def _sign_request(params: Dict, nonce: int) -> Dict:
    """
    Sign request using EIP-191 standard
    
    Steps:
    1. Normalize params (sort keys, convert to strings)
    2. Serialize to JSON string
    3. ABI encode: (json_str, user, signer, nonce)
    4. Keccak256 hash
    5. Create EIP-191 signable message
    6. Sign with private key
    7. Add signature to params
    
    Returns: Signed parameters
    """
    # Add timestamp
    params["timestamp"] = str(int(time.time() * 1000))
    params["recvWindow"] = "50000"
    
    # Normalize
    normalized = _normalize_params(params)
    json_str = json.dumps(normalized, separators=(',', ':'))
    
    # ABI encode
    encoded = encode(
        ['string', 'address', 'address', 'uint256'],
        [json_str, self.user, self.signer, nonce]
    )
    
    # Hash
    keccak_hash = Web3.keccak(encoded)
    
    # Sign
    signable = encode_defunct(hexstr=keccak_hash.hex())
    signed = Account.sign_message(signable, private_key=self.account.key)
    
    # Return with signature
    params["user"] = self.user
    params["signer"] = self.signer
    params["signature"] = '0x' + signed.signature.hex()
    params["nonce"] = nonce
    
    return params
```

### 2.6 Technical Analysis Toolkit

**File**: `backend/src/roma_trading/toolkits/technical_analysis.py`

**Indicators**:

```python
class TechnicalAnalysisToolkit:
    
    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict:
        """
        Calculate MACD indicator
        
        Returns: {
            "macd": float,           # MACD line
            "signal": float,         # Signal line
            "histogram": float       # MACD - Signal
        }
        
        Usage:
        - macd > signal: Bullish (buy signal)
        - macd < signal: Bearish (sell signal)
        - histogram increasing: Momentum strengthening
        - histogram decreasing: Momentum weakening
        """
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculate RSI (Relative Strength Index)
        
        Returns: float (0-100)
        
        Interpretation:
        - RSI > 70: Overbought
        - RSI < 30: Oversold
        - RSI 50: Neutral
        """
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int = 20) -> float:
        """
        Calculate EMA (Exponential Moving Average)
        
        Returns: float
        
        Usage:
        - Price > EMA: Bullish trend
        - Price < EMA: Bearish trend
        - EMA as dynamic support/resistance
        """
    
    @staticmethod
    def calculate_atr(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14
    ) -> float:
        """
        Calculate ATR (Average True Range)
        
        Returns: float
        
        Usage:
        - Measure volatility
        - Set stop loss levels
        - Position sizing
        """
    
    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float],
        period: int = 20,
        std_dev: int = 2
    ) -> Dict:
        """
        Calculate Bollinger Bands
        
        Returns: {
            "upper": float,          # Upper band
            "middle": float,         # Middle band (SMA)
            "lower": float           # Lower band
        }
        
        Usage:
        - Price near upper: Overbought
        - Price near lower: Oversold
        - Squeeze: Low volatility
        - Expansion: High volatility
        """
```

### 2.7 Decision Logger

**File**: `backend/src/roma_trading/core/decision_logger.py`

**Structure**:
```python
class DecisionLogger:
    def __init__(agent_id: str):
        """
        Initialize logger for agent
        Creates: logs/decisions/{agent_id}/
        """
    
    def log_decision(decision_data: Dict):
        """
        Save decision to JSON file
        
        Filename: decision_{timestamp}_{cycle}.json
        
        Content: {
            "timestamp": "2025-11-02T10:30:00",
            "cycle": 123,
            "agent_id": "deepseek-chat-v3.1",
            "account": {
                "balance": 10050.25,
                "available": 9000.00,
                "positions": [...]
            },
            "market_data": [...],
            "ai_reasoning": "...",
            "decisions": [
                {
                    "action": "open_long",
                    "symbol": "BTCUSDT",
                    "quantity": 0.001,
                    "leverage": 10,
                    "reason": "..."
                }
            ],
            "execution_results": [...]
        }
        """
    
    def get_recent_decisions(limit: int) -> List[Dict]:
        """Get N most recent decisions"""
    
    def get_last_cycle_number() -> int:
        """Get last cycle number for resuming"""
```

### 2.8 Performance Analyzer

**File**: `backend/src/roma_trading/core/performance.py`

**Metrics**:

```python
class PerformanceAnalyzer:
    
    def calculate_metrics(trades: List[Dict]) -> Dict:
        """
        Calculate performance metrics from trade history
        
        Returns: {
            # Basic Metrics
            "total_trades": int,
            "winning_trades": int,
            "losing_trades": int,
            "win_rate": float,              # %
            
            # P&L Metrics
            "total_pnl": float,
            "gross_profit": float,
            "gross_loss": float,
            "profit_factor": float,         # gross_profit / abs(gross_loss)
            
            # Risk Metrics
            "sharpe_ratio": float,          # Risk-adjusted returns
            "max_drawdown": float,          # Largest peak-to-trough decline
            "max_drawdown_pct": float,      # %
            
            # Trade Metrics
            "avg_win": float,
            "avg_loss": float,
            "avg_trade_duration": str,      # "HH:MM:SS"
            "largest_win": float,
            "largest_loss": float,
            
            # Current Status
            "current_streak": int,          # Positive for wins, negative for losses
            "equity_curve": List[float]     # Historical equity values
        }
        """
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0) -> float:
        """
        Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev of Returns
        
        Interpretation:
        - > 1.0: Good risk-adjusted returns
        - > 2.0: Very good
        - > 3.0: Excellent
        - < 1.0: Poor risk-adjusted returns
        """
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: List[float]) -> Tuple[float, float]:
        """
        Maximum Drawdown: Largest peak-to-trough decline
        
        Returns: (max_drawdown_amount, max_drawdown_pct)
        
        Usage:
        - Measure worst-case loss
        - Risk assessment
        - Strategy comparison
        """
```

---

## 3. Data Models

### 3.1 Configuration Models

**Trading Config** (`config/trading_config.yaml`):
```yaml
system:
  scan_interval_minutes: 3          # How often to scan markets
  max_concurrent_agents: 6          # Max agents running
  log_level: "INFO"                 # DEBUG, INFO, WARNING, ERROR

api:
  host: "0.0.0.0"
  port: 8080

agents:
  - id: "deepseek-chat-v3.1"
    name: "DEEPSEEK CHAT V3.1"
    enabled: true
    config_file: "config/models/deepseek-chat-v3.1.yaml"
```

**Model Config** (`config/models/{model}.yaml`):
```yaml
agent:
  id: "deepseek-chat-v3.1"
  name: "DEEPSEEK CHAT V3.1"
  description: "DeepSeek V3.1 trading agent"

llm:
  provider: "deepseek"              # deepseek, qwen, anthropic, xai, google, openai
  api_key: "${DEEPSEEK_API_KEY}"
  model: "deepseek-chat"
  temperature: 0.15                 # 0.0-1.0 (lower = more conservative)
  max_tokens: 4000

exchange:
  type: "aster"
  user: "${ASTER_USER_DEEPSEEK}"
  signer: "${ASTER_SIGNER_DEEPSEEK}"
  private_key: "${ASTER_PRIVATE_KEY_DEEPSEEK}"
  testnet: false

strategy:
  initial_balance: 10000.0
  scan_interval_minutes: 3
  max_account_usage_pct: 100
  
  default_coins:
    - "BTCUSDT"
    - "ETHUSDT"
    - "SOLUSDT"
    - "BNBUSDT"
    - "DOGEUSDT"
    - "XRPUSDT"
  
  risk_management:
    max_positions: 3
    max_leverage: 10
    max_position_size_pct: 30
    max_total_position_pct: 80
    max_single_trade_pct: 50
    max_single_trade_with_positions_pct: 30
    max_daily_loss_pct: 15
    stop_loss_pct: 3
    take_profit_pct: 10
  
  trading_style: "balanced"         # conservative, balanced, aggressive
```

### 3.2 API Response Models

**Agent Status**:
```typescript
interface AgentStatus {
  id: string;
  name: string;
  status: "running" | "stopped" | "error";
  uptime: number;                    // seconds
  cycle_count: number;
  last_decision_time: string;        // ISO timestamp
  config: {
    model: string;
    provider: string;
    trading_style: string;
  };
}
```

**Account Info**:
```typescript
interface AccountInfo {
  total_balance: number;             // USDT
  available_balance: number;
  unrealized_pnl: number;
  total_positions_value: number;
  used_percentage: number;           // %
}
```

**Position**:
```typescript
interface Position {
  symbol: string;                    // e.g., "BTCUSDT"
  side: "long" | "short";
  position_amt: number;              // Quantity
  entry_price: number;
  mark_price: number;
  unrealized_profit: number;
  pnl_percentage: number;            // %
  leverage: number;
  liquidation_price: number;
  margin_type: "cross" | "isolated";
}
```

**Decision Log**:
```typescript
interface DecisionLog {
  timestamp: string;
  cycle: number;
  agent_id: string;
  account: AccountInfo;
  market_data: MarketData[];
  ai_reasoning: string;
  decisions: Decision[];
  execution_results: ExecutionResult[];
}

interface Decision {
  action: "open_long" | "open_short" | "close" | "wait";
  symbol?: string;
  quantity?: number;
  leverage?: number;
  side?: "long" | "short";
  reason: string;
}
```

**Performance Metrics**:
```typescript
interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;                  // %
  total_pnl: number;
  gross_profit: number;
  gross_loss: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  avg_win: number;
  avg_loss: number;
  avg_trade_duration: string;
  largest_win: number;
  largest_loss: number;
  current_streak: number;
}
```

---

## 4. API Integration

### 4.1 REST API Endpoints

**Base URL**: `http://localhost:8080`

#### System
```
GET  /               - API info
GET  /health         - Health check
GET  /docs           - OpenAPI documentation
```

#### Agents
```
GET  /api/agents                      - List all agents
GET  /api/agents/{id}                 - Get agent status
GET  /api/agents/{id}/account         - Account balance
GET  /api/agents/{id}/positions       - Current positions
GET  /api/agents/{id}/performance     - Performance metrics
GET  /api/agents/{id}/analytics       - Detailed analytics
GET  /api/agents/{id}/decisions       - Decision history
GET  /api/agents/{id}/equity-history  - Equity curve data
GET  /api/agents/{id}/trades          - Trade history
```

#### Market
```
GET  /api/market/prices?symbols=BTCUSDT,ETHUSDT  - Get current prices
```

**Response Format**:
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**Error Format**:
```json
{
  "detail": "Error message",
  "status_code": 404
}
```

### 4.2 WebSocket API

**Endpoint**: `ws://localhost:8080/ws/agents/{id}`

**Message Types**:

```typescript
// Server → Client: Agent update
{
  "type": "agent_update",
  "data": {
    "agent_id": string,
    "timestamp": string,
    "account": AccountInfo,
    "positions": Position[],
    "performance": PerformanceMetrics
  }
}

// Server → Client: New decision
{
  "type": "new_decision",
  "data": DecisionLog
}

// Server → Client: Position update
{
  "type": "position_update",
  "data": {
    "symbol": string,
    "action": "opened" | "closed" | "modified",
    "position": Position
  }
}

// Client → Server: Subscribe
{
  "action": "subscribe",
  "agent_id": string
}

// Client → Server: Unsubscribe
{
  "action": "unsubscribe",
  "agent_id": string
}
```

### 4.3 Aster Finance API Integration

**Base URL**: `https://fapi.asterdex.com`

**Authentication**: EIP-191 signed requests

**Endpoints Used**:

```python
# Market Data (Public)
GET /fapi/v3/ticker/price             # Current price
GET /fapi/v3/klines                   # Historical klines
GET /fapi/v3/exchangeInfo             # Symbol info & precision

# Account (Signed)
GET /fapi/v3/balance                  # Account balance
GET /fapi/v3/positionRisk             # Current positions
GET /fapi/v1/userTrades               # Trade history

# Trading (Signed)
POST /fapi/v3/order                   # Place order
POST /fapi/v3/leverage                # Set leverage
DELETE /fapi/v3/allOpenOrders         # Cancel all orders
```

**Rate Limits**: 
- Public endpoints: 1200 requests/minute
- Signed endpoints: 600 requests/minute

---

## 5. Security Design

### 5.1 Credential Management

**Environment Variables** (`.env`):
```bash
# LLM API Keys
DEEPSEEK_API_KEY=sk-...
QWEN_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
XAI_API_KEY=xai-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-...

# Aster DEX Accounts (per model)
ASTER_USER_DEEPSEEK=0x...
ASTER_SIGNER_DEEPSEEK=0x...
ASTER_PRIVATE_KEY_DEEPSEEK=...

ASTER_USER_QWEN=0x...
ASTER_SIGNER_QWEN=0x...
ASTER_PRIVATE_KEY_QWEN=...

# ... (repeat for each model)
```

**Security Practices**:
1. Never commit `.env` to version control
2. Use `.env.example` as template
3. Rotate API keys regularly
4. Use separate accounts for each model
5. Monitor for unauthorized access

### 5.2 EIP-191 Signing

**Signature Process**:
```python
def sign_message(params: Dict, user: str, signer: str, nonce: int, private_key: str) -> str:
    """
    EIP-191 signature generation for Aster API
    
    Steps:
    1. Serialize parameters to JSON
    2. ABI encode with addresses and nonce
    3. Keccak256 hash
    4. Prefix with Ethereum message header
    5. Sign with private key
    6. Return hex signature
    """
    # Normalize params
    json_str = json.dumps(params, separators=(',', ':'))
    
    # ABI encode: (string, address, address, uint256)
    encoded = encode(['string', 'address', 'address', 'uint256'],
                     [json_str, user, signer, nonce])
    
    # Keccak256
    message_hash = Web3.keccak(encoded)
    
    # EIP-191 prefix
    signable_message = encode_defunct(hexstr=message_hash.hex())
    
    # Sign
    signed = Account.sign_message(signable_message, private_key=private_key)
    
    return '0x' + signed.signature.hex()
```

**Security Features**:
- Unique nonce per request (microsecond timestamp)
- Message hashing prevents tampering
- Private key never transmitted
- Signature validates request authenticity

### 5.3 Access Control

**API Level**:
- CORS restricted to configured origins
- Rate limiting on endpoints
- Input validation with Pydantic
- SQL injection prevention (no raw SQL)

**Application Level**:
- Agent account isolation
- Read-only API endpoints
- No remote execution capabilities
- Logging of all operations

---

## 6. Performance Optimization

### 6.1 Async Operations

**Pattern**:
```python
# Concurrent API calls
async def fetch_all_data():
    results = await asyncio.gather(
        get_account_balance(),
        get_positions(),
        get_market_price("BTCUSDT"),
        get_market_price("ETHUSDT"),
        # ... more calls
    )
    return results
```

**Benefits**:
- Reduced latency (parallel execution)
- Better resource utilization
- Faster trading cycle completion

### 6.2 Caching Strategy

**Price Precision Cache**:
```python
# Cache exchange info to avoid repeated API calls
_precision_cache: Dict[str, Dict] = {}

async def get_precision(symbol: str):
    if symbol in _precision_cache:
        return _precision_cache[symbol]
    
    # Fetch and cache
    info = await fetch_exchange_info()
    _precision_cache[symbol] = parse_precision(info)
    return _precision_cache[symbol]
```

**Decision Log Cache**:
```python
# Keep recent decisions in memory for quick access
_recent_decisions: List[Dict] = []

def get_recent_decisions(limit: int = 10):
    return _recent_decisions[-limit:]
```

### 6.3 Connection Pooling

**HTTP Client**:
```python
# Reuse connections for better performance
client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0, connect=10.0),
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10
    )
)
```

### 6.4 Trading Lock

**Concurrency Control**:
```python
# Shared lock prevents concurrent trades
trading_lock = asyncio.Lock()

async def trading_loop():
    async with trading_lock:
        # Only one agent trades at a time
        await execute_trades()
```

**Purpose**:
- Prevent race conditions
- Ensure consistent account state
- Avoid duplicate orders

---

## 7. Deployment

### 7.1 Local Deployment

**Requirements**:
- Python 3.12 or 3.13
- Node.js 18+
- 2GB RAM minimum
- 10GB disk space

**Setup**:
```bash
# Backend
cd backend
./setup.sh
cp .env.example .env
# Edit .env with credentials
./start.sh

# Frontend
cd frontend
npm install
npm run dev
```

**Process Management**:
```bash
# Using screen
screen -S roma-backend
cd backend && ./start.sh
# Ctrl+A, D to detach

screen -S roma-frontend
cd frontend && npm run dev
# Ctrl+A, D to detach

# List screens
screen -ls

# Reattach
screen -r roma-backend
```

### 7.2 Docker Deployment

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/logs:/app/logs
      - ./backend/config:/app/config
    restart: unless-stopped
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8080
    depends_on:
      - backend
    restart: unless-stopped
```

**Commands**:
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

### 7.3 Production Deployment

**Reverse Proxy** (Nginx):
```nginx
upstream backend {
    server localhost:8080;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}
```

**systemd Service** (`/etc/systemd/system/roma-backend.service`):
```ini
[Unit]
Description=ROMA Trading Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/roma-01/backend
ExecStart=/home/ubuntu/roma-01/backend/venv/bin/python -m roma_trading.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commands**:
```bash
# Enable and start
sudo systemctl enable roma-backend
sudo systemctl start roma-backend

# Check status
sudo systemctl status roma-backend

# View logs
sudo journalctl -u roma-backend -f
```

---

## 8. Monitoring and Operations

### 8.1 Logging

**Log Files**:
```
backend/logs/
├── roma_trading_2025-11-02.log       # Main log (daily rotation)
└── decisions/
    ├── deepseek-chat-v3.1/
    │   └── decision_20251102_103000_123.json
    ├── qwen3-max/
    │   └── decision_20251102_103000_45.json
    └── ...
```

**Log Levels**:
```python
# Configuration (backend/config/trading_config.yaml)
system:
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR

# Or via environment
LOG_LEVEL=DEBUG python -m roma_trading.main
```

**Log Format**:
```
2025-11-02 10:30:15.123 | INFO     | roma_trading.agents.trading_agent:trading_loop:234 - [deepseek-chat-v3.1] Starting cycle #123
2025-11-02 10:30:16.456 | INFO     | roma_trading.toolkits.aster_toolkit:get_market_price:295 - BTCUSDT: $68,450.23
2025-11-02 10:30:18.789 | INFO     | roma_trading.agents.trading_agent:_execute_decisions:399 - [deepseek-chat-v3.1] Opening LONG BTCUSDT: 0.001 @ 10x leverage
```

### 8.2 Health Monitoring

**Health Check Endpoint**:
```bash
curl http://localhost:8080/health
# Response: {"status": "healthy"}
```

**Agent Status**:
```bash
curl http://localhost:8080/api/agents
# Returns: List of agents with status
```

**Metrics to Monitor**:
- API response time
- Trading cycle duration
- Error rate
- Position count
- Account balance
- Daily P&L
- Win rate

### 8.3 Alerting

**Manual Alerts**:
```python
# Check if daily loss limit reached
if daily_loss_pct < -15:
    logger.critical(f"DAILY LOSS LIMIT REACHED: {daily_loss_pct:.2f}%")
    # Send alert (email, Telegram, etc.)
```

**Recommended Alerts**:
1. Daily loss > 10%
2. Single position loss > 5%
3. API errors > 5 in 5 minutes
4. Agent crash/restart
5. Low available balance < $5

---

## 9. Development Guide

### 9.1 Development Setup

```bash
# Backend
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -e .

# Run with debug logging
LOG_LEVEL=DEBUG python -m roma_trading.main

# Frontend
cd frontend
npm install
npm run dev
```

### 9.2 Testing

**Unit Tests**:
```bash
cd backend
pytest tests/
```

**Manual Testing**:
```bash
# Test API
curl http://localhost:8080/api/agents

# Test specific agent
curl http://localhost:8080/api/agents/deepseek-chat-v3.1/account

# Test WebSocket
wscat -c ws://localhost:8080/ws/agents/deepseek-chat-v3.1
```

### 9.3 Code Style

**Python**:
- PEP 8 compliant
- Type hints for function signatures
- Docstrings for classes and public methods
- Maximum line length: 100 characters

**TypeScript**:
- ESLint rules followed
- Consistent naming (camelCase for variables, PascalCase for components)
- Props interfaces defined
- Comments for complex logic

---

## 10. Troubleshooting

### Common Issues

**Issue**: ModuleNotFoundError: No module named 'roma_trading'
**Solution**: Activate virtual environment
```bash
cd backend
source venv/bin/activate
```

**Issue**: Python version error (DSPy not found)
**Solution**: Use Python 3.12 or 3.13, not 3.14
```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -e .
```

**Issue**: Insufficient margin error
**Solution**: Check available balance and reduce position size or leverage

**Issue**: Signature error (401/403)
**Solution**: Verify Aster DEX credentials in .env file

**Issue**: No trades happening
**Solution**: This is normal - AI is conservative and waits for high-confidence opportunities

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for complete guide.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-28 | Initial architecture design (Chinese) |
| 1.1.0 | 2025-11-02 | English translation and updates for v1.1.0 |

---

**Document Status**: ✅ Current  
**Last Updated**: November 2, 2025  
**Next Review**: When v1.2.0 features are implemented
