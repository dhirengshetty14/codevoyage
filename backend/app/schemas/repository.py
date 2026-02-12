"""Repository schemas"""

from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID


class RepositoryBase(BaseModel):
    """Base repository schema"""
    name: str
    url: str
    description: Optional[str] = None
    is_public: bool = True


class RepositoryCreate(RepositoryBase):
    """Schema for creating a repository"""
    pass


class RepositoryResponse(RepositoryBase):
    """Schema for repository response"""
    id: UUID
    clone_path: Optional[str] = None
    default_branch: str
    total_commits: int
    total_contributors: int
    total_files: int
    is_analyzed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_analyzed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
