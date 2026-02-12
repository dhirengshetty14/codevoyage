"""API routes"""

from fastapi import APIRouter
from app.api import repositories, analyses, health

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["repositories"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
