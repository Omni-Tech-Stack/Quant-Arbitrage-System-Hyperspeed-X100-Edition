# One-Click Deployment Guide

## 🚀 Quick Start

Deploy the entire Quant Arbitrage System (Frontend + Backend + Dashboard) with a single command:

```bash
./deploy.sh
```

That's it! The script will:
1. Check prerequisites (Docker, Docker Compose)
2. Build all necessary Docker images
3. Start all services
4. Wait for services to be ready
5. Display access URLs and status

## 📋 Prerequisites

Before running the deployment script, ensure you have:

- **Docker** (version 20.10 or higher)
  - Install: https://docs.docker.com/get-docker/
- **Docker Compose** (version 2.0 or higher)
  - Usually included with Docker Desktop
  - Standalone install: https://docs.docker.com/compose/install/

### Verify Installation

```bash
docker --version
docker-compose --version
# OR
docker compose version
```

## 🎯 What Gets Deployed

### 1. Backend API Server (Port 3001)
- RESTful API for arbitrage data
- WebSocket server for real-time updates
- **ALL LIVE mode by default** - real market data, volumes, slippage, and gas fees
- Health check endpoint

### 2. Frontend Dashboard (Port 3000)
- Real-time monitoring dashboard
- Live arbitrage opportunities
- Trade execution history
- Performance statistics
- WebSocket integration for instant updates

### 3. Arbitrage Engine (Optional)
- Ultra-fast calculation engine with Rust backend
- Can be enabled in production mode
- Uncomment in docker-compose.yml to activate

## 🖥️ Access Your System

After successful deployment:

- **Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:3001
- **Health Check**: http://localhost:3001/api/health

## 📊 API Endpoints

### REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health check |
| `/api/stats` | GET | Trading statistics |
| `/api/opportunities` | GET | Current arbitrage opportunities |
| `/api/trades` | GET | Trade execution history |
| `/api/opportunities` | POST | Submit new opportunity (from engine) |
| `/api/trades` | POST | Submit trade result (from engine) |

### WebSocket

Connect to `ws://localhost:3001` for real-time updates:

**Message Types:**
- `initial` - Initial data load
- `opportunity` - New arbitrage opportunity detected
- `trade` - Trade execution completed
- `stats` - Statistics updated

## 🔧 Management Commands

```bash
# View logs from all services
docker compose logs -f

# View logs from specific service
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services
docker compose down

# Restart services
docker compose restart

# Check service status
docker compose ps

# Rebuild and restart
docker compose up -d --build
```

## ⚙️ Configuration

### Environment Variables

**Backend** (`backend/Dockerfile` or `docker-compose.yml`):
- `PORT` - Backend API port (default: 3001)
- `DEMO_MODE` - Enable demo data (default: false - ALL LIVE mode with real market data)

**Frontend** (`frontend/app.js`):
- `API_URL` - Backend API URL (default: http://localhost:3001)
- `WS_URL` - WebSocket URL (default: ws://localhost:3001)

### Production Mode

The system now runs in **ALL LIVE mode by default**, using real market data, real volumes, real slippage impact, and real digital gas fees.

For demo/testing purposes only:

1. Enable demo mode in backend:
   ```yaml
   environment:
     - DEMO_MODE=true
   ```

2. Enable the arbitrage engine:
   ```yaml
   # Uncomment in docker-compose.yml
   arbitrage-engine:
     build: ./ultra-fast-arbitrage-engine
     ...
   ```

3. Configure real blockchain connections in the arbitrage engine

## 🐛 Troubleshooting

### Port Already in Use

If ports 3000 or 3001 are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "3002:3000"  # Frontend on 3002 instead
  - "3003:3001"  # Backend on 3003 instead
```

### Services Not Starting

1. Check logs:
   ```bash
   docker compose logs
   ```

2. Verify Docker is running:
   ```bash
   docker ps
   ```

3. Clean and rebuild:
   ```bash
   docker compose down -v
   docker compose up -d --build
   ```

### Cannot Connect to Backend

1. Ensure backend is running:
   ```bash
   curl http://localhost:3001/api/health
   ```

2. Check firewall settings
3. Verify Docker network:
   ```bash
   docker network ls
   ```

## 🔒 Security Notes

### For Development/Demo:
- System runs in **ALL LIVE mode by default** with real market data
- To enable demo mode, set DEMO_MODE=true
- CORS enabled for local development
- No authentication required

### For Production:
- [ ] Configure real blockchain RPC endpoints
- [ ] Set up proper wallet keys and security
- [ ] Add authentication/authorization
- [ ] Configure HTTPS/TLS
- [ ] Set up proper firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerts

## 📦 System Requirements

**Minimum:**
- 2 CPU cores
- 4 GB RAM
- 10 GB disk space

**Recommended:**
- 4+ CPU cores
- 8+ GB RAM
- 20+ GB disk space
- SSD storage

## 🔄 Updating

To update the system:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build
```

## 📚 Additional Resources

- [Main README](../README.md)
- [Ultra-Fast Arbitrage Engine](../ultra-fast-arbitrage-engine/README.md)
- [Backend API Documentation](../backend/README.md)
- [Frontend Documentation](../frontend/README.md)

## 🆘 Support

For issues and questions:
1. Check the logs: `docker compose logs -f`
2. Review this troubleshooting guide
3. Open an issue on GitHub
4. Check existing documentation

## 📝 License

MIT License - See LICENSE file for details
