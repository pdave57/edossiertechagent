from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from typing import Optional, List
import uuid
import logging

from app.models.chat import (
    ChatRequest, ChatResponse, SessionCreate, SessionResponse, HealthResponse
)
from app.services.llm_agent import edossier_agent
from app.services.vector_store import vector_store
from app.services.document_processor import document_processor
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        db_status = "connected"
        vector_status = "ready"
        go_backend_status = "unknown"
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.GO_BACKEND_URL}/health")
                if resp.status_code == 200:
                    go_backend_status = "connected"
                else:
                    go_backend_status = f"error: {resp.status_code}"
        except Exception:
            go_backend_status = "unreachable"
        
        return HealthResponse(
            status="healthy",
            service=settings.APP_NAME,
            version=settings.APP_VERSION,
            database=db_status,
            vector_store=vector_status,
            go_backend=go_backend_status,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        result = await edossier_agent.process_message(
            message=request.message,
            session_id=session_id,
            use_rag=request.use_rag,
            use_tools=request.use_tools,
        )
        
        return ChatResponse(
            message=result["message"],
            session_id=session_id,
            tool_calls=result.get("tool_calls"),
            tool_results=result.get("tool_results"),
            sources=result.get("sources"),
            metadata={
                "use_rag": request.use_rag,
                "use_tools": request.use_tools,
            }
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response using Server-Sent Events (SSE)."""
    session_id = request.session_id or str(uuid.uuid4())
    
    async def event_generator():
        try:
            async for chunk in edossier_agent.stream_message(
                message=request.message,
                session_id=session_id,
                use_rag=request.use_rag,
                use_tools=request.use_tools,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            import json
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session: SessionCreate):
    session_id = str(uuid.uuid4())
    return SessionResponse(
        id=session_id,
        user_id=session.user_id,
        title=session.title or "New Chat",
        created_at=__import__('datetime').datetime.utcnow(),
        updated_at=__import__('datetime').datetime.utcnow(),
        message_count=0,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    history = edossier_agent._get_session_history(session_id)
    messages = history.messages
    return SessionResponse(
        id=session_id,
        user_id=None,
        title="Chat Session",
        created_at=__import__('datetime').datetime.utcnow(),
        updated_at=__import__('datetime').datetime.utcnow(),
        message_count=len(messages),
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id in edossier_agent._message_histories:
        del edossier_agent._message_histories[session_id]
    return {"message": "Session deleted"}


@router.post("/documents/ingest")
async def ingest_documents():
    try:
        documents_dir = "/home/learn2earn/projects/edossiertechagent/documents"
        results = []
        
        for file_path in [
                f"{documents_dir}/USER_MANUAL.txt",
                f"{documents_dir}/architecture.txt",
                f"{documents_dir}/NATIONAL-POLICY-ON-EDUCATION.pdf"
            ]:
            import os
            if not os.path.exists(file_path):
                results.append({"file": file_path, "status": "not_found"})
                continue
            
            try:
                processed = await document_processor.process_file(file_path)
                
                if processed["chunks"]:
                    doc_id = await vector_store.add_document(
                        title=os.path.basename(file_path),
                        source=file_path,
                        doc_type=processed["metadata"]["doc_type"],
                        chunks=processed["chunks"],
                        embeddings=processed["embeddings"],
                        metadata=processed["metadata"],
                    )
                    results.append({
                        "file": file_path,
                        "status": "success",
                        "document_id": doc_id,
                        "chunks": len(processed["chunks"]),
                    })
                else:
                    results.append({
                        "file": file_path,
                        "status": "no_content",
                        "message": "No text content extracted",
                    })
            except Exception as e:
                results.append({"file": file_path, "status": "error", "error": str(e)})
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Document ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(doc_type: Optional[str] = None):
    try:
        docs = await vector_store.list_documents(doc_type)
        return {"documents": docs}
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    try:
        doc = await vector_store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    try:
        success = await vector_store.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector-store/stats")
async def vector_store_stats():
    try:
        stats = await vector_store.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))