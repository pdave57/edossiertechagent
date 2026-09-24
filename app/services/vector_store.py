from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text, func
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from typing import List, Optional, Dict, Any
import uuid
import json
import logging

from app.core.config import settings
from app.models.document import Document, DocumentChunk, DocumentChunkSchema, DocumentSchema, DocumentMetadata

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_pre_ping=True,
        )
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR(500) NOT NULL,
                    source VARCHAR(500) NOT NULL,
                    doc_type VARCHAR(100) NOT NULL,
                    doc_metadata TEXT,
                    total_chunks INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS document_embeddings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content TEXT NOT NULL,
                    embedding VECTOR({settings.VECTOR_DIMENSION}),
                    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    doc_metadata TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_document_embeddings_embedding 
                ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_document_embeddings_document_id 
                ON document_embeddings (document_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_documents_source 
                ON documents (source)
            """))
        
        logger.info("Vector store initialized successfully")
    
    async def close(self):
        await self.engine.dispose()
    
    async def add_document(
        self,
        title: str,
        source: str,
        doc_type: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        doc_id = uuid.uuid4()
        metadata_json = json.dumps(metadata) if metadata else None
        
        async with self.async_session() as session:
            doc = Document(
                id=doc_id,
                title=title,
                source=source,
                doc_type=doc_type,
                doc_metadata=metadata_json,
                total_chunks=len(chunks)
            )
            session.add(doc)
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_metadata = DocumentMetadata(
                    source=source,
                    doc_type=doc_type,
                    title=title,
                ).model_dump_json()
                
                chunk_obj = DocumentChunk(
                    id=uuid.uuid4(),
                    content=chunk,
                    embedding=embedding,
                    document_id=doc_id,
                    chunk_index=i,
                    doc_metadata=chunk_metadata
                )
                session.add(chunk_obj)
            
            await session.commit()
        
        logger.info(f"Added document {doc_id} with {len(chunks)} chunks")
        return str(doc_id)
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_doc_type: Optional[str] = None,
        filter_source: Optional[str] = None
    ) -> List[DocumentChunkSchema]:
        async with self.async_session() as session:
            # Select with cosine distance calculation
            from sqlalchemy import select, func
            from pgvector.sqlalchemy import Vector
            
            query = select(
                DocumentChunk,
                (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label('similarity')
            ).where(DocumentChunk.embedding.is_not(None))
            
            if filter_doc_type:
                query = query.join(Document).where(Document.doc_type == filter_doc_type)
            
            if filter_source:
                query = query.join(Document).where(Document.source == filter_source)
            
            query = query.order_by(
                DocumentChunk.embedding.cosine_distance(query_embedding)
            ).limit(k)
            
            result = await session.execute(query)
            rows = result.all()
            
            return [
                DocumentChunkSchema(
                    id=str(row.DocumentChunk.id),
                    content=row.DocumentChunk.content,
                    document_id=str(row.DocumentChunk.document_id),
                    chunk_index=row.DocumentChunk.chunk_index,
                    metadata=DocumentMetadata.model_validate_json(row.DocumentChunk.doc_metadata) if row.DocumentChunk.doc_metadata else None,
                    similarity=float(row.similarity) if row.similarity is not None else None
                )
                for row in rows
            ]
    
    async def get_document(self, doc_id: str) -> Optional[DocumentSchema]:
        async with self.async_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == uuid.UUID(doc_id))
            )
            doc = result.scalar_one_or_none()
            
            if doc:
                return DocumentSchema.model_validate(doc)
            return None
    
    async def list_documents(self, doc_type: Optional[str] = None) -> List[DocumentSchema]:
        async with self.async_session() as session:
            query = select(Document)
            if doc_type:
                query = query.where(Document.doc_type == doc_type)
            
            result = await session.execute(query)
            docs = result.scalars().all()
            
            return [DocumentSchema.model_validate(doc) for doc in docs]
    
    async def delete_document(self, doc_id: str) -> bool:
        async with self.async_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == uuid.UUID(doc_id))
            )
            doc = result.scalar_one_or_none()
            
            if doc:
                await session.delete(doc)
                await session.commit()
                return True
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        async with self.async_session() as session:
            doc_count = await session.execute(select(func.count(Document.id)))
            chunk_count = await session.execute(select(func.count(DocumentChunk.id)))
            embedded_count = await session.execute(
                select(func.count(DocumentChunk.id)).where(DocumentChunk.embedding.is_not(None))
            )
            
            return {
                "documents": doc_count.scalar(),
                "total_chunks": chunk_count.scalar(),
                "embedded_chunks": embedded_count.scalar(),
            }


vector_store = VectorStore()