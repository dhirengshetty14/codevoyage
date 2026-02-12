"""
CodeVoyage FastAPI Application
Main entry point for the API server
"""

import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import socketio
import structlog

from app.core.config import settings
from app.core.database import engine, Base
from app.models import Repository, Analysis, Commit, File, Contributor  # noqa: F401
from app.api import api_router
from app.core.logging import setup_logging
from app.core.rate_limiter import limiter
from app.core.cache import cache_manager
from app.core.realtime import subscribe_progress_events
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Socket.IO for real-time updates
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.ALLOWED_ORIGINS.split(','),
    logger=True,
    engineio_logger=True
)

socket_app = socketio.ASGIApp(sio)
progress_listener_task: asyncio.Task | None = None


async def _fanout_progress_events():
    while True:
        try:
            async for event in subscribe_progress_events():
                analysis_id = event.get("analysis_id")
                if not analysis_id:
                    continue
                await sio.emit("analysis_progress", event, room=f"analysis_{analysis_id}")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Progress fanout listener failed, retrying", error=str(exc))
            await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting CodeVoyage API", version=settings.VERSION)
    
    # Create database tables (in production, use Alembic migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")
    try:
        await cache_manager.connect()
    except Exception as exc:
        logger.warning("Cache connection failed during startup", error=str(exc))

    global progress_listener_task
    progress_listener_task = asyncio.create_task(_fanout_progress_events())

    yield

    # Shutdown
    if progress_listener_task:
        progress_listener_task.cancel()
        with suppress(asyncio.CancelledError):
            await progress_listener_task
    await cache_manager.disconnect()
    logger.info("Shutting down CodeVoyage API")


# Create FastAPI application
app = FastAPI(
    title="CodeVoyage API",
    description="Production-grade 3D codebase visualization and analysis platform",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": "codevoyage-api"
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount Socket.IO
app.mount("/ws", socket_app)


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info("Client connected", sid=sid)
    await sio.emit('connected', {'message': 'Connected to CodeVoyage'}, room=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info("Client disconnected", sid=sid)


@sio.event
async def subscribe_analysis(sid, data):
    """Subscribe to analysis progress updates"""
    analysis_id = data.get('analysis_id')
    if analysis_id:
        await sio.enter_room(sid, f"analysis_{analysis_id}")
        logger.info("Client subscribed to analysis", sid=sid, analysis_id=analysis_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
