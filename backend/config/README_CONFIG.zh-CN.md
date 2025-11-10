# ROMA 交易平台配置指南（中文）

> 英文版请参阅 `README_CONFIG.md`。本文提供账户中心化配置的完整中文说明。

## 快速开始

```bash
cd backend/config
# 编辑 trading_config.yaml，填写账户 / 模型 / 智能体信息
vim trading_config.yaml   # 或使用你偏好的编辑器
```

详细操作步骤参考 `QUICK_START.md`。

## 配置概览

ROMA 平台支持两种配置风格：

1. **旧版（Legacy）**：每个智能体单独一个配置文件  
2. **账户中心化（推荐）**：统一在 `trading_config.yaml` 中维护账户 / 模型 / 智能体

核心文件：

- `trading_config.yaml`：主配置文件  
- `README_CONFIG.md / README_CONFIG.zh-CN.md`：详细文档  
- `QUICK_START.md`：快速上手指导

---

## 账户中心化配置结构

```yaml
accounts:
  - id: "aster-acc-01"
    dex_type: "aster"
    user: ${ASTER_USER_01}
    signer: ${ASTER_SIGNER_01}
    private_key: ${ASTER_PRIVATE_KEY_01}
    testnet: false
    hedge_mode: false

models:
  - id: "deepseek-v3.1"
    provider: "deepseek"
    api_key: ${DEEPSEEK_API_KEY}
    model: "deepseek-chat"
    temperature: 0.15
    max_tokens: 4000

agents:
  - id: "deepseek-aster-01"
    name: "DeepSeek on Aster-01"
    enabled: true
    account_id: "aster-acc-01"
    model_id: "deepseek-v3.1"
    strategy:
      initial_balance: 10000.0
      prompt_language: "en"  # 可选：覆盖系统默认语言
      scan_interval_minutes: 3
      max_account_usage_pct: 100
      default_coins:
        - BTCUSDT
        - ETHUSDT
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
      trading_style: "balanced"
      custom_prompts:
        enabled: false
```

### 关键字段说明

#### 系统设置（`system`）

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `scan_interval_minutes` | 智能体扫描市场的间隔（分钟） | 3 |
| `max_concurrent_agents` | 并发运行的智能体数量上限 | 6 |
| `log_level` | 日志等级（DEBUG / INFO / WARNING / ERROR） | INFO |
| `prompt_language` | 系统提示词语言（`en` 或 `zh`） | en |

#### 策略基础设置

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `initial_balance` | 性能统计使用的初始资金（USDT） | 10000.0 |
| `scan_interval_minutes` | 特定智能体扫描频率 | 3 |
| `max_account_usage_pct` | 单个智能体允许占用的账户资金比例 | 100 |
| `prompt_language` | 覆盖系统级提示词语言（可选） | 继承系统设置 |
| `trading_style` | 交易风格：`conservative` / `balanced` / `aggressive` | balanced |

#### 交易品种

```yaml
default_coins:
  - BTCUSDT
  - ETHUSDT
  - SOLUSDT
  - BNBUSDT
  - DOGEUSDT
  - XRPUSDT
```

> 所有品种需以 `USDT` 结尾，实际可交易品种取决于所接入的交易所。

#### 风险管理字段

| 字段 | 说明 | 建议范围 |
|------|------|----------|
| `max_positions` | 同时持仓数量上限 | 2-5 |
| `max_leverage` | 最大杠杆倍率 | 5-10 |
| `max_position_size_pct` | 单笔仓位占账户资金比例上限 | 20-35 |
| `max_total_position_pct` | 所有仓位合计占比 | 70-85 |
| `max_single_trade_pct` | 无持仓时的单笔开仓占比 | 40-60 |
| `max_single_trade_with_positions_pct` | 有持仓时的单笔开仓占比 | 25-35 |
| `max_daily_loss_pct` | 单日最大亏损百分比（触发后停止交易） | 10-20 |
| `stop_loss_pct` / `take_profit_pct` | 止损 / 止盈比例 | 2-5 / 8-15 |

#### 自定义提示词

```yaml
custom_prompts:
  enabled: true
  trading_philosophy: "强调顺势而为，控制回撤"
  entry_preferences: "仅在EMA20上方并伴随放量时做多"
  position_management: "盈利达到2R时减仓，移动止损至保本"
  market_preferences: "避开重大数据公布前30分钟"
  additional_rules: "若出现多空信号冲突则选择观望"
```

开启后自定义内容会附加到系统提示词末尾，与原有风险规则叠加使用。

---

## 环境变量

将敏感凭证写入 `.env` / 系统环境变量，配置文件中引用变量名：

```bash
# LLM 密钥
DEEPSEEK_API_KEY=xxx
QWEN_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
XAI_API_KEY=xxx
GOOGLE_API_KEY=xxx
OPENAI_API_KEY=xxx

# Aster 账户
ASTER_USER_01=0x...
ASTER_SIGNER_01=0x...
ASTER_PRIVATE_KEY_01=...

# Hyperliquid 账户
HL_SECRET_KEY_01=...
HL_ACCOUNT_ADDRESS_01=0x...
```

---

## 迁移建议

1. **抽取账户**：将旧配置中的交易账户信息搬到 `accounts` 段落  
2. **抽取模型**：将 LLM 设置迁至 `models` 段落  
3. **创建智能体**：在 `agents` 中引用账户和模型，并复制策略参数  
4. **启用提示词语言**：在系统或策略级别设置 `prompt_language: "zh"`，即可启用中文提示词与决策输出

---

## 最佳实践

1. **一账户一智能体（生产环境）**：避免订单冲突  
2. **复用模型**：同一模型可被多个智能体引用  
3. **使用环境变量**：不要在配置文件中硬编码密钥  
4. **先上测试网**：`testnet: true` 先行验证策略  
5. **定期回顾风险参数**：根据市场波动调整杠杆、止损等指标  
6. **关注日志语言**：切换 `prompt_language` 后查看日志，确认决策文字符合预期语言

---

## 常见问题

- **“Account not found”**：确认 `account_id` 是否在 `accounts` 段落中定义  
- **“Model not found”**：确认 `model_id` 是否在 `models` 段落中存在  
- **未下单**：检查 `max_daily_loss_pct` 是否触发，或者风险参数是否过于保守  
- **提示词语言未切换**：确保系统级或策略级 `prompt_language` 已设置为 `zh`，同时重启后端或等待下一轮交易周期

---

如需更多帮助，请查阅：

- `/backend/ACCOUNT_SETUP.md`：交易所账户配置  
- `/README.md` 与 `/README.zh-CN.md`：平台总览  
- `/docs/` 目录：部署、运维、API 等专题文档


