"""
Analysis model
Stores analysis results and AI insights
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Analysis(Base):
    """Analysis results model"""
    
    __tablename__ = "analyses"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False, index=True)
    
    # Analysis metadata
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
    # Analysis results (JSON)
    file_tree_data = Column(JSON)  # 3D visualization data
    contributor_network = Column(JSON)  # Network graph data
    complexity_metrics = Column(JSON)  # Complexity heatmap data
    language_evolution = Column(JSON)  # Language timeline data
    hotspots = Column(JSON)  # File hotspots data
    
    # AI insights
    ai_insights = Column(JSON)  # GPT-4 generated insights
    patterns_detected = Column(JSON)  # Coding patterns
    team_dynamics = Column(JSON)  # Collaboration insights
    
    # Error handling
    error_message = Column(Text)
    
    # Performance metrics
    processing_time_seconds = Column(Integer)
    commits_analyzed = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    repository = relationship("Repository", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, status={self.status}, progress={self.progress}%)>"
