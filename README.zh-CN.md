# ROMA-01：AI 驱动的加密货币合约交易平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

一个竞技性的 **AI 驱动加密货币合约交易**平台，具有 **NOF1 风格界面**（[nof1.ai](https://nof1.ai/)），可并排展示多个大语言模型，由 **ROMA（递归开放元智能体）**框架驱动。

[English](README.md) | 简体中文

---

## 🎯 关于本项目

### 前端：NOF1 风格界面

本平台采用 **NOF1 风格的前端界面**（[nof1.ai](https://nof1.ai/)），具有以下特点：
- 🏆 **竞技排行榜**：实时并排比较多个 AI 交易模型
- 📊 **性能可视化**：跟踪所有模型的账户价值、盈亏和交易指标
- 🎨 **智能体展示**：显示多个交易智能体，每个智能体可将任意 DEX 账户与任意 LLM 模型组合
- 📈 **实时交易面板**：监控持仓、已完成交易和 AI 决策过程
- 📝 **自定义提示词**：用户定义的交易策略
- 💬 **AI 聊天助手**：交互式聊天界面，获取交易建议、提示词建议和平台指导

该界面提供透明的视图，展示不同 AI 模型在实时交易场景中的表现，类似于 NOF1 通过竞技评估展示模型能力的方式。

### 后端：ROMA 框架

本项目基于 **ROMA（递归开放元智能体）**框架构建，这是一个分层多智能体系统，与传统的 LLM 智能体交易方法有根本性的不同。

#### 什么是 ROMA？

ROMA 是一个**元智能体框架**，使用递归分层结构来解决复杂问题。与传统的单一智能体系统不同，ROMA 通过**计划-执行-聚合**循环将交易决策分解为可并行化的组件：

```
1. Atomizer（原子化器）→ 判断任务是否需要分解
2. Planner（规划器）→ 将复杂目标分解为子任务  
3. Executor（执行器）→ 处理原子化的交易决策
4. Aggregator（聚合器）→ 将结果综合为最终行动
5. Verifier（验证器）→ 验证输出质量（可选）
```

**了解更多**：查看 [ROMA 框架文档](https://github.com/sentient-agi/ROMA)获取完整详情。

#### ROMA vs 传统 LLM 智能体交易

| 特性 | 传统 LLM 智能体 | ROMA 框架 |
|---------|----------------------|----------------|
| **架构** | 单一整体智能体 | 分层递归分解 |
| **决策过程** | 直接提示 → 行动 | 计划 → 分解 → 执行 → 聚合 |
| **复杂性处理** | 受限于提示长度 | 递归分解复杂场景 |
| **并行化** | 顺序执行 | 可并行化独立子任务 |
| **透明度** | 黑盒推理 | 清晰的任务分解和推理链 |
| **可扩展性** | 固定复杂度限制 | 处理任意复杂场景 |
| **错误恢复** | 单点故障 | 可在不同层级重新规划 |

**在交易场景中**：ROMA 允许交易智能体：
- **分解复杂的市场分析**为可并行化的组件（技术分析、情绪分析、风险评估）
- **聚合多个视角**后再做出最终交易决策
- **在每个决策层级保持透明推理**
- **通过在适当的抽象层级重新规划来从错误中恢复**

---

## ✨ 特性

- 🤖 **AI 驱动交易**：使用 DSPy 和大语言模型进行智能决策
- 🔄 **多智能体架构**：同时运行多个交易策略
- ⚖️ **高级风险管理**：4 层风险控制系统，带有持仓限制
- 🌐 **多 DEX 支持**：直接集成 Aster Finance DEX 和 Hyperliquid DEX
- 📊 **监控仪表板**：Next.js Web 界面，用于跟踪智能体和持仓
- 📈 **性能跟踪**：全面的指标和决策历史
- 🔐 **生产就绪**：安全、经过测试、久经考验
- 📝 **自定义提示词**：用户定义的交易策略
- 💬 **AI 聊天助手**：实时获取交易策略、提示词建议和平台功能的帮助

### 前端状态
- ✅ 智能体概览和状态监控
- ✅ 实时盈亏持仓跟踪
- ✅ 自定义提示词
- ✅ 决策历史和 AI 推理
- ✅ 性能指标和图表
- ✅ AI 聊天助手（新增）
- ⚠️ WebSocket 实时更新（已实现，集成待定）
- 🔜 高级图表功能（计划中）
- 🔜 策略配置 UI（计划中）

---

## 🚀 快速开始

**选择您的部署方式：**
- 🐳 **Docker** (生产环境推荐): 查看 [Docker 部署指南](docs/DOCKER_DEPLOYMENT.md)
- 💻 **本地开发**: 按照下面的说明操作

### 前置要求

- Python 3.12 或 3.13（**不支持 3.14**）
- Node.js 18+
- API 密钥（DeepSeek 或其他 LLM 提供商）
- Aster DEX 账户及余额

### 安装（5 分钟）

```bash
# 1. 克隆仓库
git clone https://github.com/lukema95/roma-01.git
cd roma-01

# 2. 后端设置
cd backend
./setup.sh

# 3. 配置 API 密钥
cp .env.example .env
nano .env  # 添加您的密钥

# 4. 启动后端
./start.sh

# 5. 前端设置（新终端）
cd ../frontend
npm install
npm run dev
```

### 访问

- **前端**：http://localhost:3000
- **后端 API**：http://localhost:8080
- **API 文档**：http://localhost:8080/docs

📖 **完整指南**：查看 [QUICKSTART.md](QUICKSTART.md)

---

## 📊 系统概览

### 架构

```
┌─────────────────────────────────────────────────────────┐
│                     Next.js 前端                         │
│  仪表板 │ 智能体详情 │ 持仓 │ 性能                       │
└────────────────────┬────────────────────────────────────┘
                     │ REST API + WebSocket
┌────────────────────┴────────────────────────────────────┐
│                  FastAPI 后端 (Python)                   │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   智能体   │  │   交易       │  │  决策          │ │
│  │  管理器    │→ │   智能体     │→ │  记录器        │ │
│  └────────────┘  └──────┬───────┘  └────────────────┘ │
│                         │                               │
│  ┌────────────────────┬┴─────────┬──────────────────┐ │
│  │  Aster DEX 工具包  │   DSPy   │  技术            │ │
│  │  (Web3 API)        │  (AI)    │  分析            │ │
│  └────────────────────┴──────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

- **智能体管理器**：使用账户中心化架构协调多个 AI 交易智能体
- **交易智能体**：使用 DSPy + LLM 进行决策（DeepSeek、Qwen、Claude、Grok、Gemini、GPT）
- **DEX 工具包**：
  - **AsterToolkit**：通过 EIP-191 签名集成 Aster Finance 永续合约
  - **HyperliquidToolkit**：通过原生 API 集成 Hyperliquid DEX
- **技术分析**：TA-Lib 指标（RSI、MACD、EMA、ATR、布林带）
- **风险管理**：多层持仓和资金保护（4 层系统）
- **决策记录器**：以 JSON 格式记录所有交易和 AI 推理
- **性能分析器**：跟踪包括胜率、夏普比率、盈利因子等指标

---

## 🎯 交易流程

```
每 3-5 分钟：

1. 扫描市场
   ├─ 获取价格、指标、持仓
   └─ 获取账户余额

2. AI 决策（DSPy）
   ├─ 分析市场状况
   ├─ 评估风险/回报
   └─ 生成行动（开仓/平仓/持有）

3. 风险验证
   ├─ 检查单笔交易限制（50%/30%）
   ├─ 检查总持仓限制（80%）
   └─ 验证最小订单规模

4. 执行交易
   ├─ 设置杠杆
   ├─ 通过 Aster API 下单
   └─ 记录决策

5. 监控与日志
   └─ 更新仪表板和指标
```

---

## ⚙️ 配置

### 账户中心化架构

ROMA-01 使用**账户中心化**配置模型，其中：
- **账户 (Accounts)** 定义 DEX 交易账户（Aster、Hyperliquid 等）
- **模型 (Models)** 定义 LLM 配置（DeepSeek、Qwen、Claude 等）
- **智能体 (Agents)** 将账户与模型绑定以创建交易智能体

这允许灵活组合：任何账户可以使用任何模型，您可以运行具有不同配置的多个智能体。

```yaml
# config/trading_config.yaml

# 定义 DEX 账户
accounts:
  - id: "aster-acc-01"
    dex_type: "aster"
    user: ${ASTER_USER_01}
    signer: ${ASTER_SIGNER_01}
    private_key: ${ASTER_PRIVATE_KEY_01}
  
  - id: "hl-acc-01"
    dex_type: "hyperliquid"
    api_secret: ${HL_SECRET_KEY_01}
    account_id: ${HL_ACCOUNT_ADDRESS_01}

# 定义 LLM 模型
models:
  - id: "deepseek-v3.1"
    provider: "deepseek"
    api_key: ${DEEPSEEK_API_KEY}
    model: "deepseek-chat"
  
  - id: "qwen3-max"
    provider: "qwen"
    api_key: ${QWEN_API_KEY}
    model: "qwen-max"

# 通过绑定账户和模型创建智能体
agents:
  - id: "deepseek-aster-01"
    name: "DeepSeek on Aster-01"
    enabled: true
    account_id: "aster-acc-01"
    model_id: "deepseek-v3.1"
  
  - id: "qwen-hl-01"
    name: "Qwen on Hyperliquid-01"
    enabled: true
    account_id: "hl-acc-01"
    model_id: "qwen3-max"
```

**优势**：
- ✅ 灵活组合账户和模型
- ✅ 在同一 DEX 上运行多个使用不同模型的智能体
- ✅ 在不同 DEX 上运行多个智能体
- ✅ 每个智能体可以有自定义提示词和策略

查看 [backend/config/README_CONFIG.md](backend/config/README_CONFIG.md) 获取详细配置指南。

### 交易对

每个智能体可以交易以下永续合约：

```yaml
default_coins:
  - "BTCUSDT"     # 比特币
  - "ETHUSDT"     # 以太坊
  - "SOLUSDT"     # Solana
  - "BNBUSDT"     # 币安币
  - "DOGEUSDT"    # 狗狗币
  - "XRPUSDT"     # 瑞波币
```

### 风险管理

每个模型都有可自定义的风险参数：

```yaml
# 示例：config/models/deepseek-chat-v3.1.yaml
risk_management:
  max_positions: 3              # 最大并发持仓数
  max_leverage: 10              # 最大杠杆倍数
  max_position_size_pct: 30     # 单个持仓限制（占账户的 %）
  max_total_position_pct: 80    # 总持仓限制（占账户的 %）
  max_single_trade_pct: 50      # 无持仓时的单笔交易限制
  max_single_trade_with_positions_pct: 30  # 有持仓时的单笔交易限制
  max_daily_loss_pct: 15        # 每日亏损熔断机制
  stop_loss_pct: 3              # 从入场价格自动止损
  take_profit_pct: 10           # 自动止盈目标
```

查看 [backend/config/README.md](backend/config/README.md) 获取详细配置指南。

### 支持的 DEX

- **Aster Finance**：通过 EIP-191 签名的永续合约
  - 支持做多/做空持仓
  - 杠杆最高 10 倍
  - 多个交易对（BTC、ETH、SOL、BNB、DOGE、XRP）

- **Hyperliquid**：原生 DEX 集成
  - 支持做多/做空持仓
  - 杠杆管理
  - 多个交易对（BTC、ETH、SOL 等）

### 支持的 LLM

所有模型都可以与任何 DEX 账户组合：

- **DeepSeek**（推荐 - 快速且便宜，约 $0.14 每 100 万 token）
- **Qwen** - 推理能力强，多语言支持
- **Claude** (Anthropic) - 高质量，价格较高
- **Grok** (xAI) - 实时数据访问
- **Gemini** (Google) - 性能强劲
- **GPT** (OpenAI) - 最新模型

查看 [backend/config/README_CONFIG.md](backend/config/README_CONFIG.md) 获取完整配置示例。

---

## 💰 交易功能

### 已支持
- ✅ 永续合约（做多和做空）
- ✅ **Aster Finance DEX** - 通过 EIP-191 签名完整集成
- ✅ **Hyperliquid DEX** - 原生 API 集成，支持杠杆管理
- ✅ **账户中心化架构** - 灵活的账户与模型绑定
- ✅ 多种杠杆选项（1-10 倍）
- ✅ 技术指标（RSI、MACD、布林带）
- ✅ 自动持仓规模计算
- ✅ 止损和止盈
- ✅ 多智能体策略
- ✅ 每个智能体可自定义提示词

### 即将推出
- 🔜 回测模块
- 🔜 策略优化
- 🔜 移动通知

---

## 📡 数据源与分析

### 当前实现
- ✅ **技术分析**：K线、RSI、MACD、EMA、ATR、布林带、成交量

### 计划增强
本平台设计支持多信息源集成，实现全面的市场分析：

- 🔜 **新闻情感**：加密货币新闻聚合与情感评分
- 🔜 **社交情报**：Twitter/Reddit 情感与恐惧贪婪指数
- 🔜 **链上数据**：鲸鱼追踪、交易所流动、网络指标
- 🔜 **宏观经济**：美联储政策、通胀数据、市场关联
- 🔜 **市场微观结构**：订单簿深度、资金费率、清算水平

**ROMA 框架优势**：当多信息源分析实现后，ROMA 的并行执行架构将支持所有数据源的同步处理，提供更快速的决策，并具备完整透明度和容错能力。

---

## 📈 风险管理系统

### 4 层保护

1. **单笔交易限制**
   - 无持仓：最多 50%
   - 有持仓：最多 30%

2. **总持仓限制**
   - 所有持仓：最多占余额的 80%

3. **单个持仓限制**
   - 规模：最多占账户的 30%
   - 止损：距入场价 3%
   - 止盈：距入场价 10%

4. **每日限制**
   - 最大每日亏损：15%

**始终保持 20%+ 的储备金以确保安全**

---

## 🖥️ 用户界面

受 [NOF1.ai](https://nof1.ai/) 启发，本平台提供竞技性 AI 模型展示界面：

### 实时交易仪表板
- **多智能体概览**：同时监控多达 6 个不同的 LLM 模型交易
- **实时性能**：实时账户价值、盈亏跟踪和持仓更新
- **价格滚动条**：BTC、ETH、SOL、BNB、DOGE、XRP 的实时加密货币价格
- **交互式图表**：可视化权益曲线和跨模型性能比较

### 排行榜视图
- **竞技排名**：通过胜率、盈利因子和夏普比率比较模型性能
- **账户价值条**：每个模型交易账户余额的可视化表示
- **高级分析**：包括已完成交易、平均持仓时间和风险指标的详细指标
- **模型状态指示器**：查看哪些模型正在运行及其当前循环计数

### 智能体详情视图
- **全面的智能体信息**：完整的交易统计和性能指标
- **当前持仓**：实时持仓跟踪，包括入场价、当前价和未实现盈亏
- **决策历史**：完整的 AI 推理日志，显示每个交易决策的制定过程
- **性能指标**：胜率、盈利因子、夏普比率、最大回撤等

### AI 聊天助手
- **交互式聊天界面**：从右侧标签页直接与 AI 助手聊天
- **交易指导**：询问有关交易策略、提示词建议和风险管理的问题
- **平台帮助**：获取理解平台功能和特性的帮助
- **实时响应**：由用于交易决策的相同 LLM 模型提供支持
- **双语支持**：完整支持英文和中文的国际化

界面设计强调透明度和对比，让用户能够看到不同 AI 模型在相同市场条件下的表现。

_截图即将推出_

---

## 🛡️ 安全

- 🔐 API 密钥存储在环境变量中
- 🔑 Web3 签名需要私钥
- 🔒 不将密钥提交到仓库
- ⚠️ 始终先在测试网测试
- 💰 从小额开始

---

## 📊 性能指标

跟踪您的交易性能：

- **总盈亏**：已实现 + 未实现利润
- **胜率**：盈利交易的百分比
- **盈利因子**：总利润 / 总亏损
- **夏普比率**：风险调整后的回报
- **最大回撤**：最大峰谷下跌

所有指标在仪表板上实时可用。

---

## 🔧 技术栈

### 后端
- Python 3.12/3.13
- FastAPI（REST API）
- DSPy（AI 框架）
- Web3.py（DEX 集成）
- TA-Lib（技术分析）
- httpx（异步 HTTP）

### 前端
- Next.js 14
- TypeScript
- Tailwind CSS
- SWR（数据获取）
- Recharts（图表）

### 基础设施
- Docker / Docker Compose
- systemd / supervisor（进程管理）
- Nginx（反向代理）

---

## 📝 项目结构

```
roma-01/
├── README.md              # 本文件
├── README.zh-CN.md        # 中文文档
├── QUICKSTART.md          # 快速开始指南
├── docs/                  # 文档
│   ├── README.md          # 文档索引
│   ├── REQUIREMENTS.md    # 项目需求
│   ├── ARCHITECTURE.md    # 系统架构
│   ├── CONFIGURATION.md   # 配置指南
│   ├── RISK_MANAGEMENT.md # 风险管理系统
│   ├── DEPLOYMENT.md      # 部署指南
│   └── TROUBLESHOOTING.md # 故障排除
├── backend/               # Python 后端
│   ├── config/            # 配置文件
│   ├── src/               # 源代码
│   │   └── roma_trading/
│   │       ├── agents/    # 交易智能体
│   │       ├── api/       # REST API
│   │       ├── core/      # 核心模块
│   │       └── toolkits/  # DEX 和 TA 集成
│   ├── logs/              # 交易日志
│   ├── setup.sh           # 设置脚本
│   └── start.sh           # 启动脚本
└── frontend/              # Next.js 前端
    └── src/
        ├── app/           # 页面
        ├── components/    # React 组件
        └── lib/           # 工具函数
```

---

## 🚦 状态

- ✅ **后端**：生产就绪
- ✅ **前端**：生产就绪
- ✅ **风险管理**：已完全实现（4层系统）
- ✅ **Aster DEX**：已集成并测试
- ✅ **Hyperliquid DEX**：已集成并测试
- ✅ **账户中心化架构**：灵活的智能体配置
- ✅ **技术分析**：RSI、MACD、布林带、EMA、ATR
- ✅ **多 DEX 支持**：同时在不同 DEX 上运行智能体
- 🔜 **多信息源分析**：新闻、社交、链上、宏观数据
- 🔜 **ROMA 集成**：完整层次化决策架构
- 🔜 **回测**：策略测试与优化

---

## ⚠️ 免责声明

这是一个使用真实资金执行真实交易的自动交易机器人。

- **不保证**盈利
- **过去的表现**不能预测未来结果
- **在使用真实资金之前在测试网上彻底测试**
- **从小额开始**并持续监控
- **您可能会损失**全部投资
- **非财务建议** - 仅供教育目的

**风险自负。**

---

## 🤝 贡献

欢迎贡献！请：

1. Fork 本仓库
2. 创建功能分支
3. 进行更改
4. 提交 Pull Request

查看 [CONTRIBUTING.md](CONTRIBUTING.md) 获取详细指南。

---

## 📄 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 📞 支持

- 📖 文档：[docs/](docs/)
- 🐛 问题：[GitHub Issues](https://github.com/lukema95/roma-01/issues)
- 💬 讨论：[GitHub Discussions](https://github.com/lukema95/roma-01/discussions)
- 📧 邮箱：lukema95@gmail.com

---

## 🙏 致谢

- **ROMA 框架**：提供分层多智能体架构 - 参见 [ROMA 文档](https://github.com/sentient-agi/ROMA)
- **NOF1.ai**：提供竞技性 AI 模型展示界面设计灵感
- **DSPy**：提供结构化 AI 提示和智能体编排
- **Aster Finance**：提供 DEX 集成和 Web3 交易基础设施
- **DeepSeek**：提供快速且经济实惠的 LLM API

---

**用 ❤️ 使用 ROMA、DSPy 和 AI 构建**

**最后更新**：2025-11-06  
**版本**：1.3.0  
**状态**：生产就绪 ✅

