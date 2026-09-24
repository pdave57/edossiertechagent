from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


Base = declarative_base()


class DocumentChunk(Base):
    __tablename__ = "document_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    doc_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index("ix_document_embeddings_embedding", "embedding", postgresql_using="ivfflat"),
        Index("ix_document_embeddings_document_id", "document_id"),
    )


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    source = Column(String(500), nullable=False)
    doc_type = Column(String(100), nullable=False)
    doc_metadata = Column(Text, nullable=True)
    total_chunks = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentMetadata(BaseModel):
    source: str
    doc_type: str
    page: Optional[int] = None
    section: Optional[str] = None
    title: Optional[str] = None


class DocumentChunkSchema(BaseModel):
    id: str
    content: str
    document_id: str
    chunk_index: int
    metadata: Optional[DocumentMetadata] = None
    similarity: Optional[float] = None
    
    class Config:
        from_attributes = True


class DocumentSchema(BaseModel):
    id: str
    title: str
    source: str
    doc_type: str
    total_chunks: int
    created_at: datetime
    
    class Config:
        from_attributes = True