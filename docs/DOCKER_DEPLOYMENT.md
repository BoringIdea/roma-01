# Docker Deployment Guide

本指南介绍如何使用 Docker 部署 ROMA-01 Trading Platform。

[English](#english-version) | [中文](#中文版本)

---

## 中文版本

### 前置要求

- Docker (>= 20.10)
- Docker Compose (>= 2.0)
- 至少 2GB 可用磁盘空间
- Aster Finance DEX 账户和私钥
- 至少一个 LLM API Key (DeepSeek/Qwen/Claude/GPT/Gemini/Grok)

**支持的架构**:
- ✅ AMD64 (x86_64) - Intel/AMD 处理器
- ✅ ARM64 (aarch64) - Apple Silicon (M1/M2/M3), ARM 服务器

### 快速开始

#### 1. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
cp backend/.env.example .env
```

编辑 `.env` 文件，填入你的配置：

```bash
# LLM Provider API Keys (set at least one)
DEEPSEEK_API_KEY=your_deepseek_api_key
QWEN_API_KEY=your_qwen_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
XAI_API_KEY=your_xai_api_key
GOOGLE_API_KEY=your_google_api_key

# Aster Finance Accounts (suffix with _01/_02...)
ASTER_USER_01=0xYourAsterUserAddress01
ASTER_SIGNER_01=0xYourAsterSignerAddress01
ASTER_PRIVATE_KEY_01=your_aster_private_key_01

# Hyperliquid Accounts (optional)
HL_SECRET_KEY_01=your_hyperliquid_secret_key_01
HL_ACCOUNT_ADDRESS_01=0xYourHyperliquidAccountAddress01
```

> 提示：可以按需新增 `ASTER_USER_02`、`HL_SECRET_KEY_02` 等条目；不要将 `.env` 提交到版本库。

#### 2. 构建并启动服务

**启动完整服务（后端 + 前端）：**

```bash
docker-compose up -d
```

**仅启动后端：**

```bash
docker-compose up -d backend
```

#### 3. 验证部署

检查服务状态：

```bash
docker-compose ps
```

查看日志：

```bash
# 查看所有服务日志
docker-compose logs -f

# 仅查看后端日志
docker-compose logs -f backend

# 仅查看前端日志
docker-compose logs -f frontend
```

访问服务：

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8080
- **API 文档**: http://localhost:8080/docs
- **健康检查**: http://localhost:8080/health

#### 4. 验证交易智能体

后端容器启动时会根据 `backend/config/trading_config.yaml` 中的配置自动加载并运行所有交易智能体，无需手动在容器内执行额外命令。

- 通过日志确认：

  ```bash
  docker-compose logs -f backend | grep "All agents started successfully"
  ```

- 通过 API 确认：

  ```bash
  curl http://localhost:8080/api/agents
  ```

如需调整智能体配置，修改 `backend/config/trading_config.yaml` 后重启后端服务即可生效。

### 管理命令

#### 停止服务

```bash
docker-compose down
```

#### 重启服务

```bash
docker-compose restart
```

#### 重新构建

```bash
docker-compose build --no-cache
docker-compose up -d
```

#### 查看资源使用

```bash
docker stats
```

#### 清理数据

```bash
# 停止并删除容器、网络
docker-compose down

# 删除容器、网络和卷（注意：会删除所有数据！）
docker-compose down -v
```

### 仅部署后端

如果你只需要部署后端服务：

#### 方法 1: 使用 Docker Compose（推荐）

```bash
docker-compose up -d backend
```

#### 方法 2: 直接使用 Docker

```bash
# 构建镜像
cd backend
docker build -t roma-01-backend .

# 运行容器
docker run -d \
  --name roma-backend \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  --env-file ../.env \
  roma-01-backend
```

### 生产环境部署建议

#### 1. 安全配置

- **不要**在代码库中提交 `.env` 文件
- 使用 Docker Secrets 或环境变量管理敏感信息
- 定期更新 API Keys
- 启用 HTTPS/TLS

#### 2. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

#### 3. 日志管理

配置日志轮转：

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"
```

#### 4. 持久化存储

确保重要数据持久化：

```yaml
volumes:
  - ./backend/logs:/app/logs
  - ./backend/data:/app/data
  - roma-db:/app/database
```

#### 5. 反向代理

使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 多架构支持

本项目 Dockerfile 已针对多架构优化：

#### Apple Silicon (M1/M2/M3) 用户

**自动支持**，无需额外配置！Dockerfile 已包含 ARM64 支持。

首次构建可能需要 10-15 分钟（编译 TA-Lib）：

```bash
docker-compose build backend
# 请耐心等待编译完成...
```

#### x86_64 用户

正常使用，构建时间约 5-8 分钟。

#### 验证架构

```bash
# 查看当前系统架构
docker version --format '{{.Server.Arch}}'

# 查看镜像架构
docker inspect roma-demo-backend | grep Architecture
```

### 故障排查

#### ARM64: TA-Lib 编译错误

如果遇到 `cannot guess build type` 错误：

```bash
# 清理缓存并重新构建
docker-compose down
docker system prune -a
docker-compose build --no-cache backend
```

#### 容器无法启动

```bash
# 查看详细日志
docker-compose logs backend

# 检查配置文件
docker-compose config
```

#### API 连接失败

1. 检查端口是否被占用：`lsof -i :8080`
2. 检查防火墙设置
3. 验证环境变量是否正确加载

#### 智能体无法交易

1. 检查 Aster DEX 配置是否正确
2. 验证 API Keys 是否有效
3. 查看后端日志中的错误信息

#### 性能问题

```bash
# 监控资源使用
docker stats

# 检查容器健康状态
docker inspect --format='{{json .State.Health}}' roma-backend | jq
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose build
docker-compose up -d

# 验证更新
docker-compose logs -f backend
```

---

## English Version

### Prerequisites

- Docker (>= 20.10)
- Docker Compose (>= 2.0)
- At least 2GB available disk space
- Aster Finance DEX account and private key
- At least one LLM API Key (DeepSeek/Qwen/Claude/GPT/Gemini/Grok)

**Supported Architectures**:
- ✅ AMD64 (x86_64) - Intel/AMD processors
- ✅ ARM64 (aarch64) - Apple Silicon (M1/M2/M3), ARM servers

### Quick Start

#### 1. Configure Environment Variables

Create `.env` file in project root:

```bash
cp backend/.env.example .env
```

Edit `.env` file with your configuration:

```bash
# LLM Provider API Keys (set at least one)
DEEPSEEK_API_KEY=your_deepseek_api_key
QWEN_API_KEY=your_qwen_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
XAI_API_KEY=your_xai_api_key
GOOGLE_API_KEY=your_google_api_key

# Aster Finance Accounts (suffix with _01/_02...)
ASTER_USER_01=0xYourAsterUserAddress01
ASTER_SIGNER_01=0xYourAsterSignerAddress01
ASTER_PRIVATE_KEY_01=your_aster_private_key_01

# Hyperliquid Accounts (optional)
HL_SECRET_KEY_01=your_hyperliquid_secret_key_01
HL_ACCOUNT_ADDRESS_01=0xYourHyperliquidAccountAddress01
```

> Tip: add `ASTER_USER_02`, `HL_SECRET_KEY_02`, etc. when you have multiple accounts; keep `.env` out of version control.

#### 2. Build and Start Services

**Start all services (backend + frontend):**

```bash
docker-compose up -d
```

**Start backend only:**

```bash
docker-compose up -d backend
```

#### 3. Verify Deployment

Check service status:

```bash
docker-compose ps
```

View logs:

```bash
# View all service logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# View frontend logs only
docker-compose logs -f frontend
```

Access services:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

#### 4. Verify Trading Agents

The backend container automatically loads and starts every trading agent defined in `backend/config/trading_config.yaml`, so no extra CLI steps are required.

- Check logs:

  ```bash
  docker-compose logs -f backend | grep "All agents started successfully"
  ```

- Query the API:

  ```bash
  curl http://localhost:8080/api/agents
  ```

To change agent behavior, update `backend/config/trading_config.yaml` and restart the backend service.

### Management Commands

#### Stop Services

```bash
docker-compose down
```

#### Restart Services

```bash
docker-compose restart
```

#### Rebuild

```bash
docker-compose build --no-cache
docker-compose up -d
```

#### View Resource Usage

```bash
docker stats
```

#### Clean Up

```bash
# Stop and remove containers, networks
docker-compose down

# Remove containers, networks and volumes (WARNING: deletes all data!)
docker-compose down -v
```

### Backend-Only Deployment

If you only need to deploy the backend service:

#### Method 1: Using Docker Compose (Recommended)

```bash
docker-compose up -d backend
```

#### Method 2: Direct Docker

```bash
# Build image
cd backend
docker build -t roma-01-backend .

# Run container
docker run -d \
  --name roma-backend \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  --env-file ../.env \
  roma-01-backend
```

### Production Deployment Best Practices

#### 1. Security Configuration

- **DO NOT** commit `.env` files to repository
- Use Docker Secrets or environment variables for sensitive data
- Regularly rotate API Keys
- Enable HTTPS/TLS

#### 2. Resource Limits

Add resource limits in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

#### 3. Log Management

Configure log rotation:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"
```

#### 4. Persistent Storage

Ensure important data is persisted:

```yaml
volumes:
  - ./backend/logs:/app/logs
  - ./backend/data:/app/data
  - roma-db:/app/database
```

#### 5. Reverse Proxy

Use Nginx as reverse proxy:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Multi-Architecture Support

This Dockerfile is optimized for multiple architectures:

#### Apple Silicon (M1/M2/M3) Users

**Automatic support** - no extra configuration needed! ARM64 support is built-in.

First build may take 10-15 minutes (compiling TA-Lib):

```bash
docker-compose build backend
# Please be patient during compilation...
```

#### x86_64 Users

Standard usage, build time approximately 5-8 minutes.

#### Verify Architecture

```bash
# Check system architecture
docker version --format '{{.Server.Arch}}'

# Check image architecture
docker inspect roma-demo-backend | grep Architecture
```

### Troubleshooting

#### ARM64: TA-Lib Compilation Error

If you encounter `cannot guess build type` error:

```bash
# Clean cache and rebuild
docker-compose down
docker system prune -a
docker-compose build --no-cache backend
```

#### Container Won't Start

```bash
# View detailed logs
docker-compose logs backend

# Check configuration
docker-compose config
```

#### API Connection Failed

1. Check if port is already in use: `lsof -i :8080`
2. Check firewall settings
3. Verify environment variables are loaded correctly

#### Agents Can't Trade

1. Verify Aster DEX configuration is correct
2. Check API Keys are valid
3. Review backend logs for error messages

#### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check container health status
docker inspect --format='{{json .State.Health}}' roma-backend | jq
```

### Updating Deployment

```bash
# Pull latest code
git pull

# Rebuild and start
docker-compose build
docker-compose up -d

# Verify update
docker-compose logs -f backend
```

---

**Version**: 1.0  
**Last Updated**: 2025-11-03

