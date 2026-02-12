"""
Commit model
Stores Git commit information
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Commit(Base):
    """Git commit model"""
    
    __tablename__ = "commits"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False, index=True)
    contributor_id = Column(UUID(as_uuid=True), ForeignKey("contributors.id"), index=True)
    
    # Commit info
    sha = Column(String(40), nullable=False, index=True)
    message = Column(Text)
    author_name = Column(String(255), index=True)
    author_email = Column(String(255), index=True)
    
    # Statistics
    files_changed = Column(Integer, default=0)
    insertions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    
    # Timestamps
    committed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    repository = relationship("Repository", back_populates="commits")
    contributor = relationship("Contributor", back_populates="commits")
    
    # Composite indexes for performance
    __table_args__ = (
        Index('idx_repo_sha', 'repository_id', 'sha', unique=True),
        Index('idx_repo_date', 'repository_id', 'committed_at'),
        Index('idx_author_date', 'author_email', 'committed_at'),
    )
    
    def __repr__(self):
        return f"<Commit(sha={self.sha[:7]}, author={self.author_name})>"
