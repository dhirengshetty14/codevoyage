# CodeVoyage- Crazy Github Tool🚀

A production-grade 3D codebase visualization and analysis platform that transforms Git repositories into interactive, AI-powered insights.

## 🎯 Project Overview

CodeVoyage analyzes Git repositories and creates stunning 3D visualizations showing:
- **3D File Tree Evolution**: Watch your codebase grow over time
- **AI-Powered Insights**: GPT-4 analyzes patterns, team dynamics, and technical debt
- **Contributor Networks**: Visualize collaboration patterns
- **Code Complexity Heatmaps**: Identify hotspots and technical debt
- **Language Evolution**: Track technology migrations

## 🏗️ Architecture Highlights

### Distributed Systems Design
- **Celery Workers**: Parallel commit analysis across multiple workers
- **Redis Pub/Sub**: Real-time progress updates via WebSocket
- **Multi-Layer Caching**: Redis (hot) + PostgreSQL (cold) + file cache
- **Rate Limiting**: Token bucket algorithm for GitHub API (5K req/hr)
- **Async I/O**: Non-blocking git operations
- **Circuit Breaker**: Graceful degradation on service failures

### Tech Stack
**Backend:**
- FastAPI (Python) - High-performance async API
- Celery + Redis - Distributed task queue
- PostgreSQL - Primary database with optimized indexes
- PyGit2 - Fast git operations
- OpenAI GPT-4 - AI-powered insights
- Socket.io - Real-time WebSocket updates

**Frontend:**
- Next.js 14 (React) - Server-side rendering
- Three.js + React Three Fiber - 3D visualization
- D3.js - Interactive graphs
- TailwindCSS - Modern styling
- Framer Motion - Smooth animations

**Infrastructure:**
- Docker + Docker Compose
- PostgreSQL, Redis, API, Workers, Frontend containers
- Production-ready configuration

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (Windows)
- Node.js 18+
- Python 3.11+
- OpenAI API Key

### Setup

1. **Clone and configure:**
```bash
cd C:\codevoyage
copy .env.example .env
# Edit .env with your API keys
```

2. **Start all services:**
```bash
docker-compose up -d
```

3. **Access the application:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Restart Later

```powershell
.\scripts\start-local.ps1
```

Stop:

```powershell
.\scripts\stop-local.ps1
```

## 📁 Project Structure

```
codevoyage/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Core configuration
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   ├── tasks/       # Celery tasks
│   │   └── utils/       # Utilities
│   ├── tests/           # Backend tests
│   └── Dockerfile
├── frontend/            # Next.js application
│   ├── src/
│   │   ├── app/         # Next.js 14 app router
│   │   ├── components/  # React components
│   │   ├── lib/         # Utilities
│   │   └── hooks/       # Custom hooks
│   └── Dockerfile
├── docker-compose.yml   # Multi-container orchestration
└── docs/               # Documentation
```

## 🎨 Features

### 1. 3D File Tree Visualization
- Animated timeline scrubbing through git history
- File size mapped to node size
- Activity intensity shown via color gradients
- Smooth camera controls and transitions

### 2. AI-Powered Analysis
- Coding pattern detection
- Team collaboration dynamics
- Major refactor identification
- Developer habit analysis
- Technology migration tracking

### 3. Contributor Network
- Interactive D3.js force-directed graph
- Collaboration pattern visualization
- Team cluster identification
- Commit-based node sizing

### 4. Code Complexity Heatmaps
- Technical debt hotspot identification
- File churn rate analysis
- Complexity metrics overlay

### 5. Language Evolution
- Stacked area charts
- Technology migration visualization
- Historical language distribution

## 🔧 Development

### Backend Development
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Run Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 📊 Performance Considerations

- **Scalability**: Designed for 1M+ commits
- **Caching Strategy**: 3-tier caching (Redis/PostgreSQL/File)
- **Rate Limiting**: Respects GitHub API limits
- **Async Processing**: Non-blocking operations
- **Database Optimization**: Proper indexing and query optimization

## 🚢 Deployment

Deployment guides for:
- AWS (ECS + RDS + ElastiCache)
- Docker Swarm
- Kubernetes

See `docs/deployment/` for detailed instructions.

For local restart, free-tier cloud deployment, and GitHub Actions CI/CD:
- `docs/RUN_DEPLOY_CICD.md`

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is a portfolio project, but suggestions are welcome!

---

**Built with ❤️ to showcase production-grade systems design**
