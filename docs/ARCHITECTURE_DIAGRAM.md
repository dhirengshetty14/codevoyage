# CodeVoyage Architecture Diagram

## System Context

```mermaid
flowchart LR
    subgraph FE[Frontend - Next.js 14]
      UI[3D + D3 Dashboard]
      WSClient[Socket.IO Client]
    end

    subgraph API[Backend - FastAPI]
      Routes[REST + WS Gateway]
      Limiter[Token Bucket Rate Limiter]
      Cache[Cache Manager]
    end

    subgraph Workers[Distributed Workers]
      CeleryW[Celery Workers]
      CeleryB[Celery Beat]
      AI[AI Insight Service]
      Git[Git Analysis Service]
      Complexity[Complexity Service]
    end

    subgraph Data[Data Layer]
      Redis[(Redis: Broker + Hot Cache + Pub/Sub)]
      PG[(PostgreSQL: Source of Truth)]
      Repo[(Repository Clone Storage)]
    end

    UI -->|HTTP| Routes
    WSClient <-->|WebSocket| Routes
    Routes --> Limiter
    Routes --> Cache
    Routes --> PG
    Routes --> Redis

    Routes -->|enqueue tasks| CeleryW
    CeleryB --> CeleryW
    CeleryW --> Git
    CeleryW --> Complexity
    CeleryW --> AI

    CeleryW --> Redis
    CeleryW --> PG
    CeleryW --> Repo

    Redis -->|progress events| Routes
    Routes -->|broadcast updates| WSClient
```

## Container Topology (Local Docker)

- `frontend`: Next.js 14 app on `:3000`
- `api`: FastAPI + Socket.IO on `:8000`
- `celery-worker`: distributed analysis workers
- `celery-beat`: scheduled orchestration
- `flower`: Celery dashboard on `:5555`
- `postgres`: primary relational store on `:5432`
- `redis`: broker + cache + pub/sub on `:6379`

## Scaling Notes

- Scale workers locally: `docker compose up -d --scale celery-worker=4`
- For 1M+ commits, shard heavy analysis stages by repository or commit range.
- Keep Redis focused on hot keys and transient events; archive heavy results in PostgreSQL.
