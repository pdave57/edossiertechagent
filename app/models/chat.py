from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    use_rag: bool = True
    use_tools: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]
    id: str


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    content: str
    success: bool = True


class ChatResponse(BaseModel):
    message: str
    session_id: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionCreate(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    vector_store: str
    go_backend: str