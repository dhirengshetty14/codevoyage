# CodeVoyage - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- **Docker Desktop** (Windows/Mac/Linux)
- **Git** (optional, for analyzing repositories)
- **OpenAI API Key** (for AI insights)

### Step 1: Clone and Configure
```bash
# Navigate to your workspace
cd C:\codevoyage

# Copy environment template
copy .env.example .env

# Edit .env file with your API keys
# Required: OPENAI_API_KEY (for AI insights)
# Optional: GITHUB_TOKEN (for public repos)
```

### Step 2: Start All Services
```bash
# Start all containers (this may take a few minutes)
docker-compose up -d

# Check service status
docker-compose ps
```

### Step 3: Access the Application
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Celery Monitoring**: http://localhost:5555
- **Database**: localhost:5432 (PostgreSQL)

### Step 4: Analyze Your First Repository
1. Open http://localhost:3000
2. Click "Get Started" button
3. Enter a Git repository URL
4. Watch the real-time analysis progress
5. Explore 3D visualizations and AI insights

## 📁 Project Structure Overview

```
codevoyage/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Configuration and utilities
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   ├── tasks/       # Celery tasks
│   │   └── schemas/     # Pydantic schemas
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/         # Next.js 14 app router
│   │   ├── components/  # React components
│   │   ├── lib/         # Utilities and API clients
│   │   └── hooks/       # Custom hooks
│   └── package.json
├── docs/                # Documentation
├── docker-compose.yml   # Multi-service orchestration
└── README.md
```

## 🔧 Development Commands

### Backend Development
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run API server
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.tasks.celery_app worker --loglevel=info
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Docker Development
```bash
# Rebuild and start all services
docker-compose up --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📊 Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js application |
| API Server | 8000 | FastAPI backend |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache and message broker |
| Flower | 5555 | Celery monitoring dashboard |

## 🔍 API Examples

### Create Repository
```bash
curl -X POST "http://localhost:8000/api/v1/repositories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "codevoyage",
    "url": "https://github.com/yourusername/codevoyage.git",
    "description": "Code analysis platform"
  }'
```

### Start Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/analyses" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": "your-repository-id"
  }'
```

### Get Analysis Progress
```bash
curl "http://localhost:8000/api/v1/analyses/your-analysis-id"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Docker Compose Won't Start
```bash
# Check Docker Desktop is running
docker ps

# Increase Docker resources (Settings → Resources)
# Windows: Minimum 4GB RAM, 2 CPUs
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

#### 3. Frontend Not Loading
```bash
# Check Node.js dependencies
cd frontend
npm install

# Clear Next.js cache
rm -rf .next
```

#### 4. AI Insights Not Working
```bash
# Verify OpenAI API key in .env
# Check API key has GPT-4 access
# Test API key:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 5. Memory Issues
```bash
# Reduce Celery worker count
# In docker-compose.yml:
#   celery-worker:
#     deploy:
#       replicas: 1  # instead of 2

# Increase Docker memory allocation
# Docker Desktop → Settings → Resources → Advanced
```

### Logs and Debugging
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f frontend

# Check service health
curl http://localhost:8000/api/v1/health/detailed
```

## 📈 Performance Tips

### For Large Repositories
1. **Increase timeout**: Set `CELERY_TASK_TIMEOUT=7200` in `.env`
2. **Add more workers**: Increase `deploy.replicas` in `docker-compose.yml`
3. **Monitor memory**: Watch Redis and PostgreSQL memory usage
4. **Use cache**: Results are cached for 1 hour by default

### Development Performance
1. **Disable AI insights**: Set `ENABLE_AI_INSIGHTS=false` in `.env`
2. **Reduce commit limit**: Set `MAX_COMMITS_TO_ANALYZE=1000` in `.env`
3. **Use mock data**: Frontend includes mock data for development

## 🎯 Demo Repository Examples

Test with these open-source repositories:

1. **Small**: https://github.com/octocat/Spoon-Knife.git
2. **Medium**: https://github.com/fastapi/fastapi.git
3. **Large**: https://github.com/tensorflow/tensorflow.git

## 🔗 Next Steps

### Explore Features
1. **3D File Tree**: Interactive WebGL visualization
2. **Timeline Scrubbing**: Scroll through git history
3. **Contributor Network**: Visualize team collaboration
4. **AI Insights**: GPT-4 powered code analysis
5. **Real-time Updates**: Live progress during analysis

### Customize
1. **Modify themes**: Edit `frontend/tailwind.config.js`
2. **Add visualizations**: Create new components in `frontend/src/components`
3. **Extend analysis**: Add new Celery tasks in `backend/app/tasks`
4. **Custom models**: Modify database models in `backend/app/models`

### Deploy to Production
See `docs/DEPLOYMENT.md` for AWS, Azure, and Kubernetes deployment guides.

## 📞 Support

### Need Help?
1. Check the [GitHub Issues](https://github.com/codevoyage/issues)
2. Review the [Architecture Documentation](ARCHITECTURE.md)
3. Join the [Community Discord](https://discord.gg/codevoyage)

### Report Bugs
```bash
# Include:
# 1. Docker version
# 2. OS version
# 3. .env configuration (without secrets)
# 4. Error logs
# 5. Steps to reproduce
```

## 🎉 Congratulations!

You've successfully set up CodeVoyage! This project demonstrates:

✅ **Distributed Systems**: Celery workers, Redis pub/sub  
✅ **Real-time Architecture**: WebSocket, live updates  
✅ **AI Integration**: GPT-4 powered insights  
✅ **3D Visualization**: Three.js, D3.js interactive graphs  
✅ **Production Design**: Rate limiting, caching, error handling  

Perfect for showcasing to recruiters on LinkedIn and technical interviews!

---

**Next**: Try analyzing your own Git repository or explore the architecture documentation to understand the systems design decisions.