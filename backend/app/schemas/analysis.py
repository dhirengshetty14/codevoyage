"""Analysis schemas"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class AnalysisBase(BaseModel):
    """Base analysis schema"""
    repository_id: UUID


class AnalysisCreate(AnalysisBase):
    """Schema for creating an analysis"""
    pass


class AnalysisResponse(AnalysisBase):
    """Schema for analysis response"""
    id: UUID
    status: str
    progress: int
    file_tree_data: Optional[Any] = None
    contributor_network: Optional[Any] = None
    complexity_metrics: Optional[Any] = None
    language_evolution: Optional[Any] = None
    hotspots: Optional[Any] = None
    ai_insights: Optional[Any] = None
    patterns_detected: Optional[Any] = None
    team_dynamics: Optional[Any] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    commits_analyzed: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
