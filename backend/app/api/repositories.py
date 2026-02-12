"""
Repository API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import structlog

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.git_service import GitService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/", response_model=RepositoryResponse)
@limiter.limit("10/minute")
async def create_repository(
    request: Request,
    repo_data: RepositoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new repository entry"""
    try:
        # Create repository
        repository = Repository(
            name=repo_data.name,
            url=repo_data.url,
            description=repo_data.description,
            is_public=repo_data.is_public
        )
        
        db.add(repository)
        await db.commit()
        await db.refresh(repository)
        
        logger.info("Repository created", repo_id=str(repository.id), name=repository.name)
        
        return repository
    except Exception as e:
        logger.error("Failed to create repository", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create repository")


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all repositories"""
    result = await db.execute(
        select(Repository)
        .order_by(Repository.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    repositories = result.scalars().all()
    return repositories


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get repository by ID"""
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repository = result.scalar_one_or_none()
    
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return repository


@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete repository"""
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repository = result.scalar_one_or_none()
    
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    await db.delete(repository)
    await db.commit()
    
    logger.info("Repository deleted", repo_id=repository_id)
    
    return {"message": "Repository deleted successfully"}
