# Deployment Guide

How to deploy the ROMA Trading Platform to production.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Deployment](#local-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Production Checklist](#production-checklist)
6. [Monitoring](#monitoring)
7. [Maintenance](#maintenance)

---

## ✅ Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS 12+
- **Python**: 3.12 or 3.13 (NOT 3.14)
- **Node.js**: 18+ (for frontend)
- **Memory**: 2GB+ RAM
- **Storage**: 10GB+ free space
- **Network**: Stable internet connection

### Required Accounts

1. **DeepSeek API** (or other LLM provider)
   - Sign up: https://platform.deepseek.com
   - Get API key

2. **Aster DEX Account**
   - Wallet address
   - Signer address
   - Private key (for signing)

3. **Initial Capital**
   - Minimum: $10 USDT
   - Recommended: $50-100 USDT for testing

---

## 💻 Local Deployment

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd roma-01

# 2. Backend setup
cd backend
./setup.sh

# 3. Configure environment
cp .env.example .env
nano .env  # Add your keys

# 4. Start backend
./start.sh

# 5. Frontend setup (new terminal)
cd ../frontend
npm install

# 6. Start frontend
npm run dev
```

### Detailed Backend Setup

```bash
cd backend

# 1. Create virtual environment
python3.13 -m venv venv
# or: python3.12 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -e .

# 4. Configure environment
cp .env.example .env
nano .env

# Add your credentials:
# DEEPSEEK_API_KEY=sk-...
# ASTER_USER=0x...
# ASTER_SIGNER=0x...
# ASTER_PRIVATE_KEY=...

# 5. Review configuration
nano config/trading_config.yaml
nano config/models/deepseek_aggressive.yaml

# 6. Start service
python -m roma_trading.main
```

### Detailed Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure (if needed)
# Edit .env.local if backend not on localhost:8080

# 3. Development mode
npm run dev

# 4. Production build
npm run build
npm start
```

### Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
nano backend/.env

# 2. Build and start services
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop services
docker-compose down
```

### `docker-compose.yml`

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/config:/app/config
      - ./backend/logs:/app/logs
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8080
    depends_on:
      - backend
    restart: unless-stopped
```

### Manual Docker Build

```bash
# Backend
cd backend
docker build -t roma-trading-backend .
docker run -d \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  --name roma-backend \
  roma-trading-backend

# Frontend
cd frontend
docker build -t roma-trading-frontend .
docker run -d \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8080 \
  --name roma-frontend \
  roma-trading-frontend
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### EC2 Setup

```bash
# 1. Launch EC2 instance
# - Ubuntu 22.04 LTS
# - t3.medium or larger
# - 20GB EBS storage
# - Security group: ports 22, 80, 443, 8080, 3000

# 2. Connect to instance
ssh ubuntu@<instance-ip>

# 3. Install dependencies
sudo apt update
sudo apt install -y python3.12 python3.12-venv nodejs npm git

# 4. Clone and setup
git clone <repository-url>
cd roma-01
cd backend && ./setup.sh
cd ../frontend && npm install
```

#### Using AWS ECS

```yaml
# task-definition.json
{
  "family": "roma-trading",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-registry/roma-trading-backend:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DEEPSEEK_API_KEY",
          "value": "your-key"
        }
      ]
    }
  ]
}
```

### Google Cloud Platform

```bash
# 1. Create Compute Engine instance
gcloud compute instances create roma-trading \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud

# 2. SSH and setup
gcloud compute ssh roma-trading
# Follow local deployment steps
```

### DigitalOcean

```bash
# 1. Create Droplet
# - Ubuntu 22.04
# - Basic plan ($12/month or higher)
# - 2GB RAM, 1 vCPU

# 2. SSH and setup
ssh root@<droplet-ip>
# Follow local deployment steps
```

---

## ✅ Production Checklist

### Before Going Live

#### Security
- [ ] API keys stored securely (not in code)
- [ ] `.env` file gitignored
- [ ] Private keys encrypted if possible
- [ ] Firewall configured (only necessary ports)
- [ ] SSH key-based authentication (no password)
- [ ] Regular security updates enabled

#### Configuration
- [ ] Started with testnet first
- [ ] Tested with small amounts ($10-20)
- [ ] Risk limits set conservatively
- [ ] Only 1 agent enabled initially
- [ ] Leverage set to 5x or less
- [ ] Stop loss enabled (3% or less)
- [ ] Daily loss limit set (10-15%)

#### Monitoring
- [ ] Log rotation configured
- [ ] Disk space monitoring
- [ ] Process monitoring (systemd/supervisor)
- [ ] Alert system setup
- [ ] Backup strategy in place

#### Testing
- [ ] All API connections tested
- [ ] Sample trade executed successfully
- [ ] P/L calculation verified
- [ ] Stop loss tested
- [ ] Emergency stop procedure tested

---

## 📊 Monitoring

### System Monitoring

#### Using systemd

```bash
# 1. Create service file
sudo nano /etc/systemd/system/roma-trading.service

# Content:
[Unit]
Description=ROMA Trading Platform
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/roma-01/backend
Environment="PATH=/home/ubuntu/roma-01/backend/venv/bin"
ExecStart=/home/ubuntu/roma-01/backend/venv/bin/python -m roma_trading.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# 2. Enable and start
sudo systemctl enable roma-trading
sudo systemctl start roma-trading

# 3. Check status
sudo systemctl status roma-trading

# 4. View logs
sudo journalctl -u roma-trading -f
```

#### Using Supervisor

```bash
# 1. Install supervisor
sudo apt install supervisor

# 2. Create config
sudo nano /etc/supervisor/conf.d/roma-trading.conf

# Content:
[program:roma-trading]
command=/home/ubuntu/roma-01/backend/venv/bin/python -m roma_trading.main
directory=/home/ubuntu/roma-01/backend
autostart=true
autorestart=true
user=ubuntu
redirect_stderr=true
stdout_logfile=/var/log/roma-trading.log

# 3. Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start roma-trading

# 4. Check status
sudo supervisorctl status
```

### Application Monitoring

```bash
# Real-time logs
tail -f backend/logs/roma_trading_$(date +%Y-%m-%d).log

# Decision logs
ls -lh backend/logs/decisions/

# Disk usage
df -h

# Memory usage
free -h

# Process stats
ps aux | grep roma_trading
```

### Alerts Setup

```bash
# Simple email alert on errors
# Add to crontab:
*/5 * * * * grep -i error /path/to/roma_trading_*.log | mail -s "ROMA Error Alert" your@email.com

# Disk space alert
*/30 * * * * [ $(df / | tail -1 | awk '{print $5}' | sed 's/%//') -gt 80 ] && echo "Disk >80%" | mail -s "Disk Alert" your@email.com
```

---

## 🔄 Maintenance

### Daily Tasks

```bash
# Check logs
tail -100 backend/logs/roma_trading_*.log

# Verify agents running
curl http://localhost:8080/agents | jq '.[] | {id, is_running}'

# Check P/L
curl http://localhost:8080/agent/deepseek_aggressive/performance | jq .
```

### Weekly Tasks

```bash
# Review performance
# Access dashboard at http://your-server:3000

# Rotate logs (if not automatic)
cd backend/logs
gzip roma_trading_$(date -d '7 days ago' +%Y-%m-%d).log

# Clean old decision logs (keep last 30 days)
find logs/decisions/ -name "decision_*.json" -mtime +30 -delete

# Update system
sudo apt update && sudo apt upgrade -y
```

### Monthly Tasks

```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz backend/config

# Rotate API keys (recommended)
# 1. Generate new API key
# 2. Update .env
# 3. Restart service

# Review and adjust risk limits
# Based on performance and account growth
```

### Log Rotation

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/roma-trading

# Content:
/home/ubuntu/roma-01/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload roma-trading > /dev/null 2>&1 || true
    endscript
}
```

---

## 🔐 Security Hardening

### Firewall Setup

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP (if using reverse proxy)
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable

# For development, also allow:
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8080/tcp  # Backend API
```

### SSL/TLS Setup (Nginx)

```bash
# Install nginx and certbot
sudo apt install nginx certbot python3-certbot-nginx

# Configure nginx
sudo nano /etc/nginx/sites-available/roma-trading

# Content:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8080/;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/roma-trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## 🆘 Rollback Procedure

```bash
# 1. Stop services
sudo systemctl stop roma-trading
# or
docker-compose down

# 2. Restore from backup
cd /home/ubuntu
tar -xzf backup-YYYYMMDD.tar.gz

# 3. Restart services
sudo systemctl start roma-trading
# or
docker-compose up -d

# 4. Verify
curl http://localhost:8080/agents
```

---

## 📈 Scaling

### Vertical Scaling
- Increase instance size (more CPU/RAM)
- Recommended: 4GB RAM, 2 vCPU for 3+ agents

### Horizontal Scaling
- Run multiple instances with different agents
- Use load balancer for frontend
- Separate backend instances per agent

---

## ✅ Post-Deployment Verification

```bash
# 1. Check backend
curl http://localhost:8080/agents
# Should return agent list

# 2. Check frontend
curl http://localhost:3000
# Should return HTML

# 3. Check logs
tail -20 backend/logs/roma_trading_*.log
# Should show "Loaded N agents"

# 4. Test API
curl http://localhost:8080/agent/deepseek_aggressive/account
# Should return account data

# 5. Check decision making
# Wait one scan interval, check:
ls backend/logs/decisions/deepseek_aggressive/
# Should see new decision_*.json files
```

---

**Deployment Status**: Ready ✅  
**Last Updated**: 2025-10-31  
**Recommended**: Start with local deployment, then scale to cloud

