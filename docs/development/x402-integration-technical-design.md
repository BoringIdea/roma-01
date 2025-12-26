## 架构概览

roma-01 的 x402 集成同时覆盖 **Seller（服务端）** 与 **Buyer（客户端）** 两种部署形态：

- Seller：基于 FastAPI 暴露 `/x402`，由支付中间件、策略生成器、审计组件构成；
- Buyer：在本地代理循环中引入远程策略客户端，通过 x402 支付获取外部策略建议。

模块划分：

1. **API 层（Seller）**：暴露 `POST /x402`，负责请求校验、速率限制、请求追踪。
2. **x402 支付中间件（Seller）**：处理 402 往返、验证 Coinbase facilitator 支付收据、维护支付状态。
3. **策略生成器（Seller）**：整合大模型和工具包生成策略建议，并附带免责声明、支付信息。
4. **远程策略客户端（Buyer）**：包装 x402 httpx 客户端，负责发起请求、支付、重试、解析响应。
5. **代理协调层（Buyer）**：在策略阶段选择本地/远程模式，处理 fallback、日志与执行。
6. **数据存储与审计**：统一记录 requestId/paymentId/modelCallId、支付流水、远程来源等信息。
7. **配置管理**：通过环境变量或配置文件注入价格、钱包、facilitator、远程端点、模型参数等。

## 组件职责

### API 层（`backend/src/roma_trading/api/routes/x402.py`）

- 定义 pydantic 模型校验请求体。
- 检查 Header 中的 `X-X402-Receipt` 或请求体中的 `paymentReceipt`。
- 没有有效收据时返回 402 Payment Required 格式的响应（JSON 或 Problem+JSON）。
- 将带收据的请求交由策略生成服务处理。

### x402 支付中间件（`x402.fastapi.middleware.require_payment`）

- 通过配置注入价格、资产、facilitator、网络等信息。
- 首次请求返回 402 Payment Required（自动生成 payment requirements）。
- 验证 Buyer 提供的 `X-PAYMENT` header，调用 facilitator 校验/结算。
- 将验证结果写入 `request.state`，供路由层读取。

### 策略生成器（Seller，`backend/src/roma_trading/core/strategy_advisor.py`）

- 接收标准化账户信息与偏好。
- 使用提示模板构造对大模型的请求，或调用本地策略生成逻辑。
- 输出结构化策略，包括 summary、steps、riskNotes、confidence、rationale。
- 支持多模型或 fallback，输出元数据（modelId、latency）。
- 在响应中附带配置化免责声明（`STRATEGY_DISCLAIMER_TEXT`）。

### 远程策略客户端（Buyer，计划新增 `backend/src/roma_trading/core/remote_strategy_client.py`）

- 封装 `x402.clients.httpx`，自动执行 402→支付→重试流程。
- 负责加载 Buyer 配置（远程端点、钱包、网络、资产、支付上限）。
- 将 roma-01 本地的账户/持仓数据映射为 `StrategyRequest` schema。
- 解析返回的 `StrategyResponse`、`X-PAYMENT-RESPONSE`，输出标准数据结构。

### 代理协调层（Buyer，增强 `TradingAgent` 或策略调用链）

- 根据配置切换本地/远程策略生成模式。
- 若远程调用失败，支持重试或回退至本地 `StrategyAdvisor`。
- 将远程策略结果写入现有日志、执行流水。

### 审计与监控

- **日志**：在现有 `decision_logger` 基础上增加支付和策略追踪；记录 requestId、paymentId、nonce、modelCallId。
- **指标**：新增支付成功率、402 返回率、模型耗时等指标，接入现有监控（如 Prometheus）。
- **追踪**：沿用 OpenTelemetry/自定义追踪 ID，贯穿整条链路。

## 时序流程

### Seller 端时序（服务端）

```text
Buyer -> API: POST /x402 (payload)
API -> Buyer: 402 Payment Required (price, asset, network, facilitator, nonce)
Buyer -> Facilitator: pay()
Facilitator -> Buyer: paymentReceipt
Buyer -> API: POST /x402 (payload + receipt)
Middleware -> Facilitator: verify(payment)
Facilitator -> Middleware: is_valid
Middleware -> Route: attach payment details
Route -> StrategyAdvisor: generate strategy
StrategyAdvisor -> LLM: prompt -> response
LLM -> StrategyAdvisor: strategy JSON
StrategyAdvisor -> Route: structured strategy
Route -> Buyer: 200 OK (strategy, disclaimer, payment info, metadata)
```

### Buyer 端时序（客户端）

```text
Agent -> RemoteClient: requestStrategy(account context)
RemoteClient -> Seller: POST /x402 (payload)
Seller -> RemoteClient: 402 Payment Required
RemoteClient -> Wallet: sign payment authorization (EIP-3009)
RemoteClient -> Facilitator: submit payment
Facilitator -> RemoteClient: receipt/settlement
RemoteClient -> Seller: POST /x402 (payload + receipt)
Seller -> RemoteClient: 200 Strategy Response
RemoteClient -> Agent: structured strategy + disclaimer + payment metadata
Agent -> Execution: apply decisions / log results
```

## 数据模型

| 实体             | 关键字段                                                   | 说明                   |
| ---------------- | ---------------------------------------------------------- | ---------------------- |
| PaymentSession   | sessionId, nonce, price, asset, network, status, expiresAt | 跟踪支付状态与生命周期 |
| StrategyRequest  | requestId, accountPlatform, payloadHash, paymentSessionId  | 请求上下文与支付关联   |
| StrategyResponse | responseId, requestId, modelId, strategySummary, createdAt | 模型输出与元数据       |

Buyer 侧还需维护远程调用日志（requestId、paymentId、endpoint），供成本核算。

## 请求与响应规范

### Seller 侧

- Header：
  - `X-PAYMENT`：Buyer 提交的支付凭据（base64）。
  - `Idempotency-Key`：可选，用于幂等控制。
- 请求体字段：与需求文档一致，另可包含 `telemetry`（客户端版本、环境）。
- 402 响应示例：

```json
{
  "type": "https://roma.sentient.ai/errors/payment-required",
  "title": "Payment Required",
  "price": "5",
  "asset": "USDC",
  "network": "base",
  "paymentPointer": "https://facilitator.cdp.coinbase.com/payments/xyz",
  "nonce": "19f3d16c-...",
  "expiresAt": "2025-11-07T10:16:00Z"
}
```

- 200 响应：包含策略、免责声明字段、支付与 metadata，见需求示例。
- 响应头：`X-PAYMENT-RESPONSE`（base64），包含 settle 结果，可选。

### Buyer 侧

- 自动读取 Seller 返回的 402 `accepts` 字段，生成支付交易。
- 支付成功后在本地缓存支付指令与 requestId，防止重复支付。
- 将 Seller 返回的 `StrategyResponse` 映射为本地策略执行结构。

## 配置项

### Seller 相关（`Settings` / `.env`）

- `X402_ENABLED`（`x402_enabled`）：是否启用付费接口，默认 `false`。
- `X402_PRICE_USDC`（`x402_price_usdc`）：每次调用收取的 USDC 金额，默认 `5.0`，建议显式配置。
- `X402_NETWORK`（`x402_network`）：支付网络，默认 `base-sepolia`（测试网）。
- `X402_PAY_TO_ADDRESS`：接收支付的钱包地址（必填，无默认）。
- `X402_PAYMENT_DESCRIPTION` / `X402_RESOURCE_DESCRIPTION` / `X402_RESOURCE_MIME_TYPE`：用于生成 payment requirements 的元信息。
- `X402_FACILITATOR_URL`：可选，自定义 facilitator URL；未配置时使用 SDK 默认。
- `X402_CDP_API_KEY_ID` / `X402_CDP_API_KEY_SECRET`：使用 Coinbase 托管 facilitator 时的 Bearer 鉴权信息。
- `X402_MAX_DEADLINE_SECONDS`（`x402_max_deadline_seconds`）：支付有效期，默认 `120` 秒。
- `X402_DISCOVERABLE`（`x402_discoverable`）：是否参与 discovery，默认 `True`。
- `STRATEGY_MODEL_ID`、`STRATEGY_PROMPT_TEMPLATE`：本地策略模型选择与提示模板路径。
- `STRATEGY_DISCLAIMER_TEXT`：响应中附带的免责声明（已提供默认文案，可自定义）。

### Buyer 相关（新增）

- `REMOTE_STRATEGY_ENABLED`：是否启用远程策略模式，默认 `false`。
- `REMOTE_X402_ENDPOINT`：目标 Seller `/x402` 完整 URL（必填，启用时校验）。
- `REMOTE_X402_NETWORK`：远程支付网络（可选，未配置时使用 Seller 提示）。
- `REMOTE_X402_PAYMENT_ASSET`：远程支付资产，默认 `USDC`。
- `REMOTE_X402_ACCOUNT`：Buyer 钱包地址（启用时必填）。
- `REMOTE_X402_PRIVATE_KEY`：Buyer 钱包私钥或签名代理，建议通过密钥管理注入。
- `REMOTE_X402_PRICE_CAP`：单次调用最大愿付费用（可选，用于成本控制）。
- `REMOTE_X402_DISCOVERY`：facilitator discovery endpoint（可选，用于动态发现 Seller）。
- `REMOTE_FALLBACK_MODE`：失败兜底策略，默认 `local`（回退至本地模型）。
- `REMOTE_TIMEOUT_SECONDS`：远程调用超时时间，默认 `10` 秒。
- `REMOTE_RETRY_LIMIT`：远程调用重试次数，默认 `1`。

所有配置通过 `.env`、`trading_config.yaml` 或密钥管理系统注入，避免硬编码；Buyer 私钥等敏感信息需使用安全存储。

## 安全设计

### Seller

- 对请求体进行 JSON schema 校验，限制字段大小与类型。
- 验证支付收据时校验 nonce、金额、防止重放；使用缓存或数据库记录已消费收据。
- 可选：要求 Buyer 提供附加签名或 API Key，结合速率限制。
- 审计日志中对敏感数据（余额、仓位）脱敏或加密。

### Buyer

- 私钥通过环境变量、安全存储或远程签名服务加载，不写入仓库。
- 支付交易前进行价格/资产校验，避免超出预算。
- 全程使用 HTTPS，验证远程服务证书，防止中间人攻击。
- 记录远程 disclaimer 与来源，保障合规。

## 错误处理与重试

### Seller

- 支付验证失败：返回 402 + 具体 `error`/`errorCode`（如 `invalid_receipt`、`expired`、`amount_mismatch`）。
- 模型超时：返回 503/504，保留 paymentSession，提示 Buyer 稍后重试。
- 内部错误：返回 500，附 `traceId`，记录日志并告警。

### Buyer

- 支付失败：根据 facilitator 返回的错误码重试或回退；必要时提示用户补充余额。
- 网络/超时：按 `REMOTE_RETRY_LIMIT` 重试，依然失败则根据 `REMOTE_FALLBACK_MODE` 处理。
- 解析失败：若远程返回不可解析，记录原始响应并回退到本地模型/等待模式。

## 测试策略

### 单元测试

- Seller：支付指令生成、facilitator 校验逻辑、策略 JSON 解析、免责声明字段。
- Buyer：远程请求构造、支付头生成、响应解析、错误回退。

### 集成测试

- Seller：使用 sandbox facilitator 演示 402→支付→200 闭环，验证 settle 与响应头。
- Buyer：模拟远程服务器，确保自动支付与策略解析可用；覆盖失败重试与 fallback。
- Buyer+Seller：端到端测试（本地起 Seller + 本地 Buyer 调用）。

### 负载与安全

- Seller：评估高并发支付验证/模型调用；测试重放、伪造收据、异常 payload。
- Buyer：压力测试连续多次远程调用的超时与重试；验证密钥泄露防护与错误处理。

## 开发计划

1. **MVP（Sprint 1）**：
   - 完成 Seller `/x402` 路由、支付中间件配置、本地策略生成、日志记录。
   - 完成 Buyer 远程客户端基础调用与策略落地。
2. **增强（Sprint 2）**：
   - Seller：完善审计、指标、错误码、配置化价格。
   - Buyer：增加重试/回退策略、超时监控、成本追踪。
3. **扩展（Sprint 3）**：
   - 多模型、多计费、discovery 动态发现服务、策略聚合与比较。
   - 支持多远程端点路由与 SLA 监控。

## 未决问题

- Coinbase facilitator 的认证方式（已确定使用 CDP API Key Bearer 鉴权）。
- 模型服务调用限额与成本控制策略（当前阶段暂不设置限额，由运营监控实际消耗）。
- 是否需要对策略输出进行合规审核或免责声明处理（已确定通过 `STRATEGY_DISCLAIMER_TEXT` 字段在响应中附带标准免责声明）。
- Hyperliquid/Aster 数据格式差异对通用 schema 的影响（通过统一的公共 schema + 平台适配器映射字段，需在实现阶段完善映射规则）。
- Buyer fallback 策略与成本预算管理方式（是否需要自动限额或多服务端路由）。
- Buyer 私钥管理标准（是否引入远程签名服务或硬件钱包）。

## 实现进度（2025-11）

- ✅ Seller `/x402` 路由、支付中间件接入、策略响应（含免责声明/支付信息）
- ✅ 配置化的 Seller 参数（价格、地址、facilitator、模型）
- ✅ 文档与需求更新（Seller/Buyer 双模式说明）
- ⏳ Buyer 远程策略客户端、代理调用逻辑、回退策略（计划中）
- ⏳ 指标监控、审计增强、discovery 集成（计划中）


