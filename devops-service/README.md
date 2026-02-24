# 🚀 DevOps Platform - Complete Integrated Package

**Full-Stack DevOps Automation with Frontend & Backend in ONE Package**

## 📦 What's Inside

```
devops-integrated/
├── frontend/               # React Dashboard (Port 3000)
├── api-gateway/           # API Gateway (Port 8000)
├── agents/
│   ├── build-agent/       # Docker Builder (Port 8001)
│   └── github-agent/      # GitHub Importer (Port 8007)
├── shared/                # Common utilities
├── docker-compose.yml     # ALL services
└── .env.example           # Configuration
```

## 🚀 ONE COMMAND DEPLOYMENT

```bash
docker-compose up -d
```

**That's it!** All 7 services start together:
- ✅ Frontend (http://localhost:3000)
- ✅ API Gateway (http://localhost:8000)
- ✅ Build Agent (http://localhost:8001)
- ✅ GitHub Agent (http://localhost:8007)
- ✅ MongoDB (localhost:27017)
- ✅ Redis (localhost:6379)
- ✅ RabbitMQ (http://localhost:15672)

## 📊 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | React Dashboard |
| **API Gateway** | http://localhost:8000 | Central API |
| **API Docs** | http://localhost:8000/docs | Swagger |
| **Build Agent** | http://localhost:8001 | Docker Builder |
| **GitHub Agent** | http://localhost:8007 | Project Importer |
| **RabbitMQ UI** | http://localhost:15672 | Queue (devops/devops123) |

## 🎯 Quick Start

### 1. Start Everything
```bash
docker-compose up -d
```

### 2. Access Dashboard
```
http://localhost:3000
```

### 3. Connect GitHub
1. Go to GitHub page
2. Paste your GitHub token
3. Import projects

### 4. Build Projects
1. Go to Projects
2. Click "Build"
3. Monitor in Builds page

## 🔧 Development

### View Logs
```bash
docker-compose logs -f
```

### Restart Service
```bash
docker-compose restart frontend
```

### Stop All
```bash
docker-compose down
```

### Rebuild
```bash
docker-compose build --no-cache
docker-compose up -d
```

## ✅ Features

### Frontend (React)
- Dashboard with service health
- GitHub integration UI
- Project management
- Build monitoring
- Settings panel

### Backend (FastAPI)
- API Gateway routing
- Docker image building
- GitHub project import
- MongoDB persistence
- Real-time monitoring

## 🎉 Everything Works Together!

Frontend → API Gateway → Build/GitHub Agents → MongoDB

**One package, one command, complete platform!**
