# Run, Deploy, and CI/CD (CodeVoyage)

This is the exact path to:
- restart locally after closing everything,
- deploy to a low-cost/free-tier setup,
- push to your GitHub and enable continuous CI/CD.

## 1. Start Again Locally

From project root:

```powershell
.\scripts\start-local.ps1
```

Useful commands:

```powershell
.\scripts\logs-local.ps1
.\scripts\logs-local.ps1 api
.\scripts\stop-local.ps1
```

Manual equivalents:

```powershell
docker compose up -d --build
docker compose ps
docker compose logs -f api
docker compose down
```

## 2. Push to GitHub (`dhirengshetty14`)

No remote is configured yet in this repo, so do this once:

1. Create a new empty repo on GitHub (for example `codevoyage`).
2. Run:

```powershell
git add .
git commit -m "feat: production analytics dashboard + 3d explorer + ci/cd setup"
git branch -M main
git remote add origin https://github.com/dhirengshetty14/codevoyage.git
git push -u origin main
```

If remote already exists later:

```powershell
git push
```

## 3. Free-Tier Cloud Deployment (Practical)

Recommended split:
- `Frontend`: Vercel (free hobby tier)
- `Backend API + Celery worker + Postgres + Redis`: Render free-tier path (or lowest paid fallback if free not available for DB in your account/region)

### 3.1 Deploy Frontend on Vercel

1. Import your GitHub repo in Vercel.
2. Project root: `frontend`
3. Framework: Next.js
4. Add env vars:
   - `NEXT_PUBLIC_API_URL=https://<your-api-domain>`
   - `NEXT_PUBLIC_WS_URL=https://<your-api-domain>`
   - `NEXT_PUBLIC_WS_PATH=/ws/socket.io`
5. Deploy.

### 3.2 Deploy Backend + Worker on Render

Create services from the same repo:

1. `Web Service` for API:
   - Root directory: `backend`
   - Dockerfile: `backend/Dockerfile`
   - Start command:
     `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. `Worker Service` for Celery:
   - Root directory: `backend`
   - Dockerfile: `backend/Dockerfile`
   - Start command:
     `celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1 --pool=solo`

3. Provision Postgres and Redis on Render (or compatible managed alternatives).

4. Set these env vars on both API and worker:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `CELERY_BROKER_URL` (same as Redis URL)
   - `CELERY_RESULT_BACKEND` (same as Redis URL)
   - `TEMP_STORAGE_PATH=/tmp/repos`
   - `LOG_LEVEL=INFO`
   - `ENABLE_AI_INSIGHTS=false` (or `true` + set `OPENAI_API_KEY`)
   - `OPENAI_API_KEY` (optional)
   - `ALLOWED_ORIGINS=https://<your-vercel-domain>`

5. Validate:
   - API health: `https://<api-domain>/health`
   - Frontend can create analysis jobs.

## 4. GitHub Actions CI/CD Already Added

Workflows now in repo:

- `.github/workflows/ci.yml`
  - Backend: install deps, run pytest, compile checks
  - Frontend: type-check + production build
  - Runs on pull requests and pushes to `main` / `develop`

- `.github/workflows/cd.yml`
  - On push to `main`, triggers:
    - Render API deploy hook
    - Render worker deploy hook
    - Vercel production deploy via Vercel CLI

## 5. Required GitHub Repository Secrets

Go to GitHub repo -> Settings -> Secrets and variables -> Actions -> New repository secret.

For Render:
- `RENDER_API_DEPLOY_HOOK_URL`
- `RENDER_WORKER_DEPLOY_HOOK_URL`

For Vercel:
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

After secrets are added:
1. Push to `main`.
2. CI runs first.
3. CD deploys automatically.

## 6. Fast Recovery Checklist

If app seems down:

1. `docker compose ps`
2. `.\scripts\logs-local.ps1 api`
3. `.\scripts\logs-local.ps1 celery-worker`
4. `.\scripts\logs-local.ps1 frontend`
5. `docker compose up -d --build`

