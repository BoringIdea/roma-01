/**
 * Internationalization translations for ROMA-01
 */

export const translations = {
  en: {
    // Header
    header: {
      live: "Live",
      leaderboard: "Leaderboard",
      models: "Models", // Keep for backward compatibility
      agents: "Agents",
      about: "About",
      settings: "Settings",
      running: "RUNNING",
    },
    
    // Home page
    home: {
      loading: "Loading trading platform...",
      failedToLoad: "Failed to load agents",
    },
    
    // Leaderboard
    leaderboard: {
      title: "LEADERBOARD",
      overallStats: "OVERALL STATS",
      advancedAnalytics: "ADVANCED ANALYTICS",
      accountValue: "ACCOUNT VALUE",
      winningModel: "WINNING MODEL",
      totalEquity: "TOTAL EQUITY",
      netDeposits: "Net Deposits",
      adjustedEquity: "Deposit-Adjusted Equity",
      activePositions: "ACTIVE POSITIONS",
      noActivePositions: "No active positions",
      noData: "No data",
      noRunningAgents: "No running agents",
      startAgent: "Start an agent to see leaderboard",
      rank: "RANK",
      model: "MODEL",
      balance: "BALANCE",
      pnl: "P&L",
      pnlPercent: "P&L %",
      margin: "MARGIN",
      avgLeverage: "AVG LEVERAGE",
      avgConfidence: "AVG CONFIDENCE",
      winRate: "WIN RATE",
      biggestWin: "BIGGEST WIN",
      biggestLoss: "BIGGEST LOSS",
      sharpe: "SHARPE",
      trades: "TRADES",
      acctValue: "ACCT VALUE ↓",
      avgTradeSize: "AVG TRADE SIZE",
      medianTradeSize: "MEDIAN TRADE SIZE",
      avgHold: "AVG HOLD",
      medianHold: "MEDIAN HOLD",
      expectancy: "EXPECTANCY",
      medianLeverage: "MEDIAN LEVERAGE",
      returnPercent: "RETURN %",
      totalPnl: "TOTAL P&L",
      fees: "FEES",
      medianConfidence: "MEDIAN CONFIDENCE",
      note: "Note:",
      completedTradesNote: "All statistics (except Account Value and P&L) reflect completed trades only. Active positions are not included in calculations until they are closed.",
    },
    
    // Right Side Tabs
    tabs: {
      positions: "POSITIONS",
      trades: "TRADES",
      decisions: "DECISIONS",
      prompts: "PROMPTS",
      chat: "CHAT",
      analysis: "ANALYSIS",
      filter: "FILTER:",
      allAgents: "ALL AGENTS",
      selectAgent: "SELECT AGENT:",
      noPositions: "No open positions",
      noTrades: "No completed trades yet",
      noDecisions: "No decisions yet",
      // Multi-DEX filters
      filterDex: "DEX:",
      filterAccount: "ACCOUNT:",
      allDex: "ALL DEX",
      allAccounts: "ALL ACCOUNTS",
      aster: "Aster",
      hyperliquid: "Hyperliquid",
    },
    
    // Chart strings
    charts: {
      accountValue: "Account Value",
      noEquityData: "No equity data available yet",
      tradingNotStarted: "Data will appear after trading starts",
    },
    
    // Positions
    positions: {
      symbol: "Symbol",
      side: "Side",
      entry: "Entry",
      current: "Current",
      pnl: "P/L",
      leverage: "Leverage",
      long: "LONG",
      short: "SHORT",
    },
    
    // Trades
    trades: {
      time: "Time",
      symbol: "Symbol",
      side: "Side",
      entry: "Entry",
      exit: "Exit",
      pnl: "P/L",
      quantity: "Qty",
    },
    
    // Decisions
    decisions: {
      cycle: "Cycle",
      time: "Time",
      actions: "Actions",
      expand: "Expand",
      collapse: "Collapse",
    },
    
    // Prompt Editor
    prompts: {
      title: "CUSTOM PROMPTS",
      subtitle: "Customize AI trading strategy",
      enable: "Enable",
      viewFullPrompt: "View Full Prompt",
      hidePreview: "Hide Preview",
      clearAll: "Clear All",
      savePrompts: "Save Prompts",
      saving: "Saving...",
      clearing: "Clearing...",
      saved: "✓ Saved Successfully",
      loading: "Loading...",
      loadingPrompts: "Loading prompts...",
      noRunningAgents: "No running agents",
      startAgentPrompt: "Start an agent to configure prompts",
      confirmClear: "Are you sure you want to clear all custom prompts?",
      copiedToClipboard: "Copied to clipboard!",
      effectNextCycle: "✓ Prompts saved! Will take effect in next trading cycle.",
      tip: "💡 Tip: Custom prompts are appended to core system rules. Changes take effect in the next trading cycle.",
      
      // Field labels
      tradingPhilosophy: "Trading Philosophy",
      entryPreferences: "Entry Preferences",
      positionManagement: "Position Management",
      marketPreferences: "Market Preferences",
      additionalRules: "Additional Rules",
      
      // Placeholders (English examples)
      philosophyPlaceholder: `Example:
Core goal: Maximize Sharpe ratio
- Quality over quantity, only trade with high conviction
- Be patient, let profits run
- Avoid frequent trading and overtrading`,
      
      entryPlaceholder: `Example:
Entry criteria:
- Multi-dimensional cross-validation (price + volume + indicators)
- Confidence ≥ 75 to open positions
- Avoid single-dimension signals and ranging markets`,
      
      positionPlaceholder: `Example:
Position management:
- Hold winning positions for at least 30 minutes
- Let profits run, cut losses quickly
- Avoid overtrading (max 0.2 trades per hour)`,
      
      marketPlaceholder: `Example:
Long-short balance:
- Uptrend → Long
- Downtrend → Short
- No bias towards long!`,
      
      additionalPlaceholder: `Example:
- Max 2 trades per hour
- Take 30-min break after 2 consecutive losses
- Risk-reward ≥ 1:3
- Better to miss than make low-quality trades`,
      
      characters: "characters",
      fullSystemPromptPreview: "Full System Prompt Preview",
      copy: "Copy",
    },
    
    // Chat
    chat: {
      welcome: "Chat with AI Assistant",
      exampleQuestions: "Ask me anything about trading strategies, prompts, platform features, or request token analysis.",
      example1: "What are some basic trading prompt suggestions?",
      example2: "How does risk management work in this platform?",
      example3: "Analyze BTC",
      example4: "What should I do with ETH?",
      placeholder: "Type your message...",
      send: "Send",
      thinking: "Thinking...",
      errorMessage: "Failed to get response. Please try again.",
    },
    
    // Agent Detail
    agent: {
      totalAccountValue: "Total Account Value",
      totalPnl: "Total P&L",
      netRealized: "Net Realized",
      availableCash: "Available Cash",
      totalFees: "Total Fees",
      winRate: "Win Rate",
      profitFactor: "Profit Factor",
      sharpeRatio: "Sharpe Ratio",
      maxDrawdown: "Max Drawdown",
      totalTrades: "Total Trades",
      avgWin: "Avg Win",
      avgLoss: "Avg Loss",
      avgLeverage: "Avg Leverage",
      avgConfidence: "Avg Confidence",
      holdTimes: "HOLD TIMES",
      long: "Long",
      short: "Short",
      flat: "Flat",
      activePositions: "ACTIVE POSITIONS",
      last25Trades: "LAST 25 TRADES",
      recentDecisions: "RECENT DECISIONS",
      currentPositions: "CURRENT POSITIONS",
      completedTrades: "COMPLETED TRADES",
      noPositions: "No open positions",
      noTrades: "No completed trades yet",
      noDecisions: "No decisions yet",
      symbol: "Symbol",
      side: "Side",
      entry: "Entry",
      current: "Current",
      quantity: "Quantity",
      leverage: "Leverage",
      margin: "Margin",
      pnl: "P/L",
      exit: "Exit",
      time: "Time",
      cycle: "Cycle",
      actions: "Actions",
      expand: "Expand",
      collapse: "Collapse",
      reasoning: "Reasoning:",
      loadingStats: "Loading statistics...",
      doesNotIncludeFees: "Does not include funding costs and rebates",
      entryTime: "Entry Time",
      entryPrice: "Entry Price",
      exitPrice: "Exit Price",
      holdingTime: "Holding Time",
      notionalEntry: "Notional Entry",
      notionalExit: "Notional Exit",
      liquidationPrice: "Liquidation Price",
      unrealizedPnl: "Unrealized P&L",
      totalUnrealizedPnl: "Total Unrealized P&L:",
    },
    
    // About page
    about: {
      title: "ROMA-01",
      
      // Paragraphs
      intro: `ROMA-01 is an AI-powered cryptocurrency futures trading platform for running multiple LLM-based agents in live markets. It combines automated trading with a full-featured monitoring dashboard, leaderboard, and AI assistant services, all powered by the ROMA (Recursive Open Meta-Agents) framework.`,
      
      multiModel: `The platform allows you to run up to 6 different AI models simultaneously—DeepSeek, Qwen, Claude, Grok, Gemini, and GPT—each managing its own independent trading account on live cryptocurrency futures markets. You can observe how different models trade BTC, ETH, SOL, BNB, DOGE, and XRP perpetual futures under the same market conditions.`,
      
      nof1Interface: `The frontend focuses on operational transparency rather than simple model comparison. You can monitor account values, P/L, open positions, completed trades, and decision logs for each agent, and quickly understand how AI-driven trading impacts overall portfolio risk and performance.`,
      
      romaFramework: `Under the hood, ROMA-01 is built on the ROMA Framework, a meta-agent system that fundamentally differs from traditional LLM agent trading approaches. Instead of a single monolithic agent, ROMA uses hierarchical recursive decomposition to structure complex trading decisions into manageable components.`,
      
      romaProcess: `ROMA processes tasks through a structured loop: an Atomizer decides if task decomposition is needed; a Planner breaks complex goals into subtasks; Executors handle atomic trading decisions; an Aggregator synthesizes results into final actions; and a Verifier (optional) validates output quality. This creates clear task decomposition and transparent reasoning chains at each level of decision-making.`,
      
      tradingContext: `In trading contexts, ROMA decomposes complex market analysis into components like technical analysis, sentiment, and risk assessment. It aggregates multiple perspectives before making final trading decisions, maintains transparent reasoning at each abstraction level, and can re-plan at different levels to recover from errors—capabilities that traditional monolithic agents cannot match.`,
      
      platformFeatures: `ROMA-01 includes a 4-layer risk management system with position limits, direct Web3 integration with Aster Finance and Hyperliquid DEXs, comprehensive technical analysis using TA-Lib indicators (RSI, MACD, EMA, ATR, Bollinger Bands), complete decision history logging with AI reasoning for every trade, and an AI chat assistant that also supports token analysis requests.`,
      
      quote: "Hierarchical recursive decomposition and multi-agent design enable ROMA-01 to trade complex markets with transparency and control.",
      
      // Section titles
      romaVsTraditional: "ROMA vs Traditional LLM Agent Trading",
      traditionalAgent: "Traditional LLM Agent",
      romaFrameworkTitle: "ROMA Framework",
      platformFeaturesTitle: "Platform Features",
      
      // Traditional agent list
      traditional: {
        monolithic: "Single monolithic agent",
        directPrompt: "Direct prompt → action",
        limitedByPrompt: "Limited by prompt length",
        sequential: "Sequential execution",
        blackBox: "Black box reasoning",
        fixedComplexity: "Fixed complexity limit",
        singlePoint: "Single point of failure",
      },
      
      // ROMA framework list
      roma: {
        hierarchical: "Hierarchical recursive decomposition",
        planExecute: "Plan → decompose → execute → aggregate",
        breaksDown: "Recursively breaks down complexity",
        parallelizes: "Parallelizes independent subtasks",
        clearReasoning: "Clear reasoning chains",
        arbitraryComplexity: "Handles arbitrary complexity",
        rePlan: "Re-plan at different levels",
      },
      
      // Features list
      features: {
        aiTrading: "AI-Driven Trading using DSPy and large language models",
        multiAgent: "Multi-Agent Architecture: Run 6 trading strategies simultaneously",
        riskManagement: "Advanced Risk Management: 4-layer risk control system",
        web3Integration: "Web3 Integration: Direct connection to Aster Finance DEX",
        leaderboard: "Real-time competitive leaderboard with win rates, profit factors, Sharpe ratios",
        performance: "Performance tracking with comprehensive metrics and decision history",
        technicalAnalysis: "Technical analysis: RSI, MACD, EMA, ATR, Bollinger Bands",
        productionReady: "Production ready: Secure, tested, and battle-hardened",
      },
      
      footer: "Open Source • MIT License • Built with ROMA, DSPy, and AI",
    },
  },
  
  zh: {
    // Header
    header: {
      live: "实时",
      leaderboard: "排行榜",
      models: "模型", // Keep for backward compatibility
      agents: "智能体",
      about: "关于",
      settings: "设置",
      running: "运行中",
    },
    
    // Home page
    home: {
      loading: "加载交易平台中...",
      failedToLoad: "加载智能体失败",
    },
    
    // Leaderboard
    leaderboard: {
      title: "排行榜",
      overallStats: "总体统计",
      advancedAnalytics: "高级分析",
      accountValue: "账户价值",
      winningModel: "最佳模型",
      totalEquity: "总账户权益",
      netDeposits: "净充值",
      adjustedEquity: "调整后账户权益",
      activePositions: "当前持仓",
      noActivePositions: "暂无持仓",
      noData: "暂无数据",
      noRunningAgents: "无运行中的智能体",
      startAgent: "启动智能体以查看排行榜",
      rank: "排名",
      model: "模型",
      balance: "余额",
      pnl: "盈亏",
      pnlPercent: "盈亏率",
      margin: "保证金",
      avgLeverage: "平均杠杆",
      avgConfidence: "平均信心",
      winRate: "胜率",
      biggestWin: "最大盈利",
      biggestLoss: "最大亏损",
      sharpe: "夏普比率",
      trades: "交易数",
      acctValue: "账户价值 ↓",
      avgTradeSize: "平均交易额",
      medianTradeSize: "中位交易额",
      avgHold: "平均持仓",
      medianHold: "中位持仓",
      expectancy: "期望值",
      medianLeverage: "中位杠杆",
      returnPercent: "收益率",
      totalPnl: "总盈亏",
      fees: "手续费",
      medianConfidence: "中位信心",
      note: "注意：",
      completedTradesNote: "除账户价值和盈亏外，所有统计数据仅反映已完成交易。活跃持仓在平仓前不计入统计。",
    },
    
    // Right Side Tabs
    tabs: {
      positions: "持仓",
      trades: "交易",
      decisions: "决策",
      prompts: "提示词",
      chat: "聊天",
      analysis: "分析",
      filter: "筛选：",
      allAgents: "所有智能体",
      selectAgent: "选择智能体：",
      noPositions: "暂无持仓",
      noTrades: "暂无已完成交易",
      noDecisions: "暂无决策记录",
      // Multi-DEX filters
      filterDex: "DEX：",
      filterAccount: "账户：",
      allDex: "所有 DEX",
      allAccounts: "所有账户",
      aster: "Aster",
      hyperliquid: "Hyperliquid",
    },
    
    // Chart strings
    charts: {
      accountValue: "账户权益",
      noEquityData: "暂无账户权益数据",
      tradingNotStarted: "交易开始后将显示数据",
    },
    
    // Positions
    positions: {
      symbol: "币种",
      side: "方向",
      entry: "入场",
      current: "当前",
      pnl: "盈亏",
      leverage: "杠杆",
      long: "做多",
      short: "做空",
    },
    
    // Trades
    trades: {
      time: "时间",
      symbol: "币种",
      side: "方向",
      entry: "入场",
      exit: "出场",
      pnl: "盈亏",
      quantity: "数量",
    },
    
    // Decisions
    decisions: {
      cycle: "周期",
      time: "时间",
      actions: "操作",
      expand: "展开",
      collapse: "收起",
    },
    
    // Prompt Editor
    prompts: {
      title: "自定义提示词",
      subtitle: "定制 AI 交易策略",
      enable: "启用",
      viewFullPrompt: "查看完整提示词",
      hidePreview: "隐藏预览",
      clearAll: "清空全部",
      savePrompts: "保存提示词",
      saving: "保存中...",
      clearing: "清空中...",
      saved: "✓ 保存成功",
      loading: "加载中...",
      loadingPrompts: "加载提示词中...",
      noRunningAgents: "无运行中的智能体",
      startAgentPrompt: "启动智能体以配置提示词",
      confirmClear: "确定要清空所有自定义提示词吗？",
      copiedToClipboard: "已复制到剪贴板！",
      effectNextCycle: "✓ 提示词已保存！将在下一个交易周期生效。",
      tip: "💡 提示：自定义提示词将附加到核心系统规则之后，修改将在下一个交易周期生效。",
      
      // Field labels
      tradingPhilosophy: "交易哲学",
      entryPreferences: "开仓偏好",
      positionManagement: "持仓管理",
      marketPreferences: "市场偏好",
      additionalRules: "额外规则",
      
      // Placeholders (Chinese examples)
      philosophyPlaceholder: `示例：
核心目标：最大化夏普比率
- 质量优于数量，只在高确信度时交易
- 耐心持仓，让利润奔跑
- 避免频繁交易和过度进出`,
      
      entryPlaceholder: `示例：
开仓标准：
- 多维度交叉验证（价格+量+指标+形态）
- 信心度 ≥ 75 才开仓
- 避免单一维度信号和横盘震荡`,
      
      positionPlaceholder: `示例：
持仓管理：
- 盈利持仓至少持有30分钟
- 让利润奔跑，快速止损
- 避免过度交易（每小时最多0.2笔）`,
      
      marketPlaceholder: `示例：
做多做空平衡：
- 上涨趋势 → 做多
- 下跌趋势 → 做空
- 不要有做多偏见！`,
      
      additionalPlaceholder: `示例：
- 每小时最多2次交易
- 连续亏损2次后休息30分钟
- 风险回报比 ≥ 1:3
- 宁可错过，不做低质量交易`,
      
      characters: "字符",
      fullSystemPromptPreview: "完整系统提示词预览",
      copy: "复制",
    },
    
    // Chat
    chat: {
      welcome: "与 AI 助手聊天",
      exampleQuestions: "问我关于交易策略、提示词、平台功能，或请求代币分析的任何问题。",
      example1: "有哪些基本的交易提示词建议？",
      example2: "这个平台的风险管理是如何工作的？",
      example3: "分析 BTC",
      example4: "ETH 现在应该怎么操作？",
      placeholder: "输入您的消息...",
      send: "发送",
      thinking: "思考中...",
      errorMessage: "获取回复失败，请重试。",
    },
    
    // Agent Detail
    agent: {
      totalAccountValue: "账户总价值",
      totalPnl: "总盈亏",
      netRealized: "净已实现",
      availableCash: "可用资金",
      totalFees: "总手续费",
      winRate: "胜率",
      profitFactor: "盈利因子",
      sharpeRatio: "夏普比率",
      maxDrawdown: "最大回撤",
      totalTrades: "总交易数",
      avgWin: "平均盈利",
      avgLoss: "平均亏损",
      avgLeverage: "平均杠杆",
      avgConfidence: "平均信心",
      holdTimes: "持仓时间",
      long: "做多",
      short: "做空",
      flat: "空仓",
      activePositions: "活跃持仓",
      last25Trades: "最近25笔交易",
      recentDecisions: "最近决策",
      currentPositions: "当前持仓",
      completedTrades: "已完成交易",
      noPositions: "暂无持仓",
      noTrades: "暂无已完成交易",
      noDecisions: "暂无决策记录",
      symbol: "币种",
      side: "方向",
      entry: "入场",
      current: "当前",
      quantity: "数量",
      leverage: "杠杆",
      margin: "保证金",
      pnl: "盈亏",
      exit: "出场",
      time: "时间",
      cycle: "周期",
      actions: "操作",
      expand: "展开",
      collapse: "收起",
      reasoning: "推理：",
      loadingStats: "加载统计数据中...",
      doesNotIncludeFees: "不包含资金费用和返佣",
      entryTime: "入场时间",
      entryPrice: "入场价",
      exitPrice: "出场价",
      holdingTime: "持仓时长",
      notionalEntry: "入场名义",
      notionalExit: "出场名义",
      liquidationPrice: "强平价",
      unrealizedPnl: "未实现盈亏",
      totalUnrealizedPnl: "总未实现盈亏：",
    },
    
    // About page
    about: {
      title: "ROMA-01",
      
      // Paragraphs
      intro: `ROMA-01 是一个 AI 驱动的加密货币合约交易平台，可在真实市场中运行多个基于 LLM 的交易智能体，结合完整的监控仪表板、排行榜和 AI 助手服务，由 ROMA（递归开放元智能体）框架驱动。`,
      
      multiModel: `本平台允许你同时运行多达 6 个不同的 AI 模型——DeepSeek、Qwen、Claude、Grok、Gemini 和 GPT——每个模型管理自己独立的交易账户，在实时加密货币合约市场上交易。你可以在相同市场环境下观察不同模型如何交易 BTC、ETH、SOL、BNB、DOGE 和 XRP 等永续合约。`,
      
      nof1Interface: `前端界面以交易运营透明度为核心，而不是简单的模型对比。你可以查看每个智能体的账户价值、盈亏、当前持仓、已完成交易和详细决策日志，快速理解 AI 交易行为对整体账户风险和收益的影响。`,
      
      romaFramework: `在底层，ROMA-01 基于 ROMA 框架构建，这是一个与传统 LLM 智能体交易方法根本不同的元智能体系统。它并非依赖单一整体智能体，而是通过分层递归分解，将复杂的交易决策结构化为可管理的子任务。`,
      
      romaProcess: `ROMA 通过一个结构化循环处理任务：原子化器判断是否需要任务分解；规划器将复杂目标拆解为子任务；执行器处理原子化的交易决策；聚合器将结果综合为最终行动；验证器（可选）用于校验输出质量。这样在每个决策层级都形成了清晰的任务分解与透明的推理链。`,
      
      tradingContext: `在交易场景中，ROMA 会把复杂的市场分析分解为技术分析、情绪分析、风险评估等多个组件，在做出最终交易决策前聚合多种视角，并在每个抽象层级保持透明推理。必要时可以在不同层级重新规划，以从错误中恢复——这些能力是传统整体智能体难以实现的。`,
      
      platformFeatures: `ROMA-01 提供带持仓限制的 4 层风险管理系统、与 Aster Finance 和 Hyperliquid DEX 的直接 Web3 集成、基于 TA-Lib 指标（RSI、MACD、EMA、ATR、布林带）的全面技术分析、每笔交易的完整决策历史与 AI 推理记录，以及支持代币分析请求的 AI 聊天助手。`,
      
      quote: "分层递归分解与多智能体设计，让 ROMA-01 能够在复杂市场中以透明且可控的方式进行交易。",
      
      // Section titles
      romaVsTraditional: "ROMA vs 传统 LLM 智能体交易",
      traditionalAgent: "传统 LLM 智能体",
      romaFrameworkTitle: "ROMA 框架",
      platformFeaturesTitle: "平台功能",
      
      // Traditional agent list
      traditional: {
        monolithic: "单一整体智能体",
        directPrompt: "直接提示 → 行动",
        limitedByPrompt: "受限于提示长度",
        sequential: "顺序执行",
        blackBox: "黑盒推理",
        fixedComplexity: "固定复杂度限制",
        singlePoint: "单点故障",
      },
      
      // ROMA framework list
      roma: {
        hierarchical: "分层递归分解",
        planExecute: "计划 → 分解 → 执行 → 聚合",
        breaksDown: "递归分解复杂性",
        parallelizes: "并行化独立子任务",
        clearReasoning: "清晰推理链",
        arbitraryComplexity: "处理任意复杂度",
        rePlan: "在不同层级重新规划",
      },
      
      // Features list
      features: {
        aiTrading: "AI 驱动交易：使用 DSPy 和大语言模型",
        multiAgent: "多智能体架构：同时运行 6 个交易策略",
        riskManagement: "高级风险管理：4 层风险控制系统",
        web3Integration: "Web3 集成：直接连接 Aster Finance DEX",
        leaderboard: "实时竞技排行榜，包含胜率、盈利因子、夏普比率",
        performance: "性能跟踪，包含全面的指标和决策历史",
        technicalAnalysis: "技术分析：RSI、MACD、EMA、ATR、布林带",
        productionReady: "生产就绪：安全、经过测试、久经考验",
      },
      
      footer: "开源 • MIT 许可证 • 使用 ROMA、DSPy 和 AI 构建",
    },
  },
};

export type Language = "en" | "zh";

export function getTranslation(lang: Language) {
  return translations[lang];
}

