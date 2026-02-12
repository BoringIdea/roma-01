## 项目背景

roma-01 作为多链量化交易智能体平台，当前通过后端策略引擎与多种 DEX 工具包（例如 Hyperliquid、Aster）为用户提供交易服务。为了实现按调用计费、降低外部集成门槛，并让其他节点复用已有的模型能力，需要引入 Coinbase 的 x402 支付协议。目标是同时支持：

- **Seller**：本地部署 roma-01，暴露付费 `POST /x402` 接口，对外提供策略建议；
- **Buyer**：本地部署 roma-01，但不运行大模型，通过 x402 支付调用他人暴露的 `/x402`，获取策略建议后交由本地代理执行。

参考官方文档：<https://docs.cdp.coinbase.com/x402/welcome>

## 项目目标

1. 在 roma-01 后端暴露 `POST /x402` 接口，提供按次付费的策略建议服务。
2. 集成 x402 支付流程，仅在支付成功后调用本地大模型和策略逻辑。
3. 支持 Hyperliquid、Aster 持仓/余额等上下文的标准化输入与提示构造。
4. 建立日志、审计、监控能力，追踪支付与模型调用的生命周期。
5. 支持 roma-01 作为 Buyer，通过 x402 调用远程 `/x402` 接口获取策略建议。
6. 在 Buyer 模式下，将远程返回的建议与本地执行/日志模块打通，支持回退到本地模型。
7. 为未来扩展多资产、多计费策略、多服务端选择预留配置。

## 角色与用户故事

### 角色

- **外部调用方（第三方 Buyer）**：希望通过简单的 HTTP 请求购买一次策略建议服务。
- **roma-01 平台（Seller 模式）**：提供付费访问的策略建议接口，同时确保安全与风控。
- **roma-01 平台（Buyer 模式）**：部署者不运行本地模型，通过付费调用其他 Seller 获取策略建议，再由本地代理执行。
- **运营/风控人员**：需要审计支付记录、模型输出，排查异常。

### 核心用户故事

1. 作为第三方或 Buyer，我可以携带账户持仓数据调用任意部署的 `POST /x402`，在支付完成后得到策略建议。
2. 作为 Seller，我可以确保只对已支付请求调用本地大模型，控制计算成本并避免滥用。
3. 作为 Buyer 模式的 roma-01 用户，我可以在本地配置远程 `x402` 端点与私钥，无需运行大模型即可获得策略建议。
4. 作为运营人员，我可以通过日志和监控信息回溯每一次付费请求、支付结算与策略输出。

## 功能范围

### 必须实现

1. **Server（Seller）能力**：
   - 请求规范化：定义账户、持仓、偏好、目标等字段并进行 schema 校验。
   - x402 支付交互：返回 402 Payment Required（包含价格、网络、facilitator、nonce 等）；校验 receipt，确认金额、nonce、过期时间；防重放、防重复支付。
   - 策略生成：使用本地大模型与工具包生成结构化策略建议。
   - 响应规范：包含 `strategy`、`disclaimer`、`payment`、`metadata`。
   - 可观测性：记录 requestId/paymentId/modelCallId，输出日志、指标、追踪信息。
2. **Client（Buyer）能力**：
   - 在配置远程 `/x402` 端点、钱包地址与私钥后，自动完成 402→支付→重试流程。
   - 发送与本地一致的 `StrategyRequest` 数据结构，兼容 Hyperliquid/Aster。
   - 解析返回的策略建议与 `X-PAYMENT-RESPONSE` 结算信息，写入本地日志流水。
   - 支持失败兜底（重试、本地模型 fallback、人工提示）。

### 可选/后续实现

- 支持多级计费（按模型、按市场、按响应大小）。
- 引入积分或订阅机制，以降低频繁支付的摩擦。
- 提供策略回放或模拟执行接口。
- 扩展更多链上资产或 facilitator。

### 非范围

- 不负责代为执行交易或持久化账户秘钥。
- 不提供 Web 前端入口，仅提供 API。
- 不涉及用户注册或身份验证流程（除可选签名验证）。

## 业务流程

### Seller 流程

1. Buyer 首次调用 `POST /x402`（无支付收据）。
2. 服务返回 402 Payment Required，附带支付指令（价格、资产、network、facilitator、nonce、截止时间）。
3. Buyer 按指令完成链上支付，获取支付收据。
4. Buyer 携带收据再次调用 `POST /x402`。
5. 服务端调用 facilitator 验证收据，确认金额、nonce、deadline；成功后调用本地大模型生成策略。
6. 返回 200 响应，包括策略建议、免责声明、支付信息、metadata。
7. 写入日志、指标、支付流水，供审计监控。

### Buyer 流程

1. 本地 roma-01 配置远程 `REMOTE_X402_ENDPOINT`、钱包地址与私钥。
2. 策略生成阶段检查配置，若启用远程模式，构造 `StrategyRequest`（含持仓、余额等）。
3. 通过 `x402` 客户端发送请求，若收到 402，则自动根据支付指令签名授权并提交交易。
4. 支付结算成功后自动重试，获取策略响应。
5. 本地记录策略、支付信息，交由执行引擎处理；若失败，按配置回退到本地模型或返回等待。

## 请求与响应示例

### 请求体（示例）

```json
{
  "account": {
    "platform": "hyperliquid",
    "positions": [
      { "symbol": "ETH-PERP", "size": 1.2, "entryPx": 3150.5 },
      { "symbol": "BTC-PERP", "size": -0.5, "entryPx": 62000 }
    ],
    "balance": { "asset": "USDC", "amount": 2500 }
  },
  "preferences": {
    "leverage": 3,
    "riskTolerance": "medium",
    "timeHorizon": "24h"
  },
  "objectives": "Optimize delta-neutral coverage while preserving upside",
  "symbols": ["ETH-PERP", "BTC-PERP", "BNB-PERP"]
}
```

### 成功响应

```json
{
  "strategy": {
    "summary": "Reduce ETH long exposure by 25% and hedge BTC short with call options",
    "steps": [
      "Close 0.3 ETH perpetual long to reduce exposure",
      "Open 0.2 BTC perpetual long to neutralize downside",
      "Set conditional order: buy 0.1 BTC if price drops 3%"
    ],
    "riskNotes": [
      "Monitor funding rate shifts over the next 6h",
      "Consider additional collateral if volatility spikes"
    ]
  },
  "payment": {
    "receiptId": "fac-20251107-123456",
    "amount": "5",
    "asset": "USDC",
    "network": "base"
  },
  "metadata": {
    "requestId": "req-2f7b9",
    "model": "roma-gpt-strategy-v1",
    "generatedAt": "2025-11-07T10:15:00Z"
  }
}
```

## 非功能性需求

- **性能**：
  - Seller：支付验证 + 模型生成总耗时 ≤ 5s；模型阶段可配置超时与重试。
  - Buyer：远程调用超时时间 ≤ 10s，可配置重试与断路策略。
- **可用性**：
  - Seller：服务可用性 ≥ 99.5%，支付失败需返回可重试信息。
  - Buyer：远程服务不可达时，需在 1 分钟内切换至 fallback 或告警。
- **安全**：
  - Seller：输入校验、防重放；敏感字段脱敏或加密；可选买方签名验证。
  - Buyer：私钥存储于安全介质，支付授权过程加密；敏感配置不写入仓库。
- **审计**：
  - Seller：保存 ≥ 90 天的请求、支付、模型日志。
  - Buyer：记录远程 requestId/paymentId/disclaimer，满足成本核算与追溯。
- **配置与默认值**：
  - Seller 侧 `x402_enabled` 默认 `false`，需要显式配置收款地址、价格、网络、facilitator URL 等；所有值从环境变量/配置文件读取，避免硬编码。
  - Buyer 侧 `remote_strategy_enabled` 默认 `false`，启用后需提供远程端点、钱包地址/私钥、网络与预算；同样通过配置文件或环境变量注入。

## 依赖与前置条件

- 获取 Coinbase x402 facilitator 凭据与 Base 网络支付配置（Seller）。
- 获取或配置 Buyer 钱包地址与私钥，确保具备所需链上资产（Buyer）。
- 确定 roma-01 内部使用的大模型接口（本地或外部服务），并评估成本与 SLA。
- 整理 Hyperliquid、Aster 工具包提供的数据字段，确保与请求体对齐。
- 准备测试网或 sandbox 环境，验证 Seller 402 支付闭环及 Buyer 自动支付流程。

## 验收标准

1. 提供演示脚本（HTTPie/Postman）完成 Seller 侧 402→支付→200 流程。
2. Seller 402 响应包含完整支付指令；支付成功后返回策略建议、免责声明、支付信息。
3. Buyer 侧提供示例脚本/CLI，演示自动支付并获取策略建议。
4. 日志中能够关联 requestId、paymentId、modelCallId，并记录远程调用来源。
5. 关键配置（价格、facilitator、模型 ID、远程端点、私钥等）可通过环境变量或配置中心管理。
6. 至少一条 Seller 集成测试与一条 Buyer 集成测试验证端到端流程。

## 风险与缓解

- **支付延迟或失败**：Seller 返回可重试信息，Buyer 提供重试/回退逻辑；必要时缓存支付状态。
- **模型不可用或响应质量低**：Seller 设置熔断/降级；Buyer 支持切换至本地模型或提示等待。
- **数据泄露**：限制输入字段、脱敏敏感信息；Buyer 私钥保护、请求加密传输。
- **监管合规**：Seller 在响应中加入标准免责声明；Buyer 显示远程 disclaimer 并记录来源。
- **跨主体依赖**：Buyer 需评估远程服务 SLA 与成本，必要时配置多服务端或 discovery 以分散风险。


