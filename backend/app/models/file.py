"""
File model
Stores file information and metrics
"""

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class File(Base):
    """File model with complexity metrics"""
    
    __tablename__ = "files"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False, index=True)
    
    # File info
    path = Column(String(1024), nullable=False, index=True)
    filename = Column(String(255), index=True)
    extension = Column(String(50), index=True)
    
    # Size metrics
    size_bytes = Column(Integer, default=0)
    lines_of_code = Column(Integer, default=0)
    
    # Complexity metrics
    cyclomatic_complexity = Column(Float)
    cognitive_complexity = Column(Float)
    maintainability_index = Column(Float)
    
    # Activity metrics
    total_commits = Column(Integer, default=0)
    total_contributors = Column(Integer, default=0)
    churn_rate = Column(Float)  # How often file changes
    
    # Timestamps
    first_seen_at = Column(DateTime(timezone=True))
    last_modified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    repository = relationship("Repository", back_populates="files")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_repo_path', 'repository_id', 'path', unique=True),
        Index('idx_repo_ext', 'repository_id', 'extension'),
        Index('idx_complexity', 'cyclomatic_complexity'),
        Index('idx_churn', 'churn_rate'),
    )
    
    def __repr__(self):
        return f"<File(path={self.path}, complexity={self.cyclomatic_complexity})>"
