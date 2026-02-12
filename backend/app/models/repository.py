"""
Repository model
Stores information about analyzed Git repositories
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Repository(Base):
    """Git repository model"""
    
    __tablename__ = "repositories"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Repository info
    name = Column(String(255), nullable=False, index=True)
    url = Column(String(512), nullable=False)
    clone_path = Column(String(512))
    
    # Metadata
    description = Column(Text)
    default_branch = Column(String(100), default="main")
    total_commits = Column(Integer, default=0)
    total_contributors = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    
    # Status
    is_public = Column(Boolean, default=True)
    is_analyzed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_analyzed_at = Column(DateTime(timezone=True))
    
    # Relationships
    analyses = relationship("Analysis", back_populates="repository", cascade="all, delete-orphan")
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    files = relationship("File", back_populates="repository", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Repository(id={self.id}, name={self.name})>"
