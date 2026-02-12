"""
Contributor model
Stores contributor information and statistics
"""

from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Contributor(Base):
    """Contributor model"""
    
    __tablename__ = "contributors"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Contributor info
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    
    # Statistics
    total_commits = Column(Integer, default=0)
    total_insertions = Column(Integer, default=0)
    total_deletions = Column(Integer, default=0)
    total_files_changed = Column(Integer, default=0)
    
    # Activity
    first_commit_at = Column(DateTime(timezone=True))
    last_commit_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    commits = relationship("Commit", back_populates="contributor")
    
    # Indexes
    __table_args__ = (
        Index('idx_email_unique', 'email', unique=True),
        Index('idx_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Contributor(name={self.name}, commits={self.total_commits})>"
