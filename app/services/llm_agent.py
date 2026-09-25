from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_agent
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables import RunnableConfig
from typing import Dict, Any, List, Optional, AsyncGenerator
import logging
import json

from app.core.config import settings
from app.tools.langchain_tools import GO_BACKEND_TOOLS
from app.services.vector_store import vector_store
from app.services.document_processor import document_processor

logger = logging.getLogger(__name__)


class EdossierAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            streaming=True,
        )
        
        self.tools = GO_BACKEND_TOOLS
        
        self.system_prompt = """You are an AI assistant for the e-Dossier Student Information System (SIS) and School Management platform.

You have access to:
1. A knowledge base containing the e-Dossier User Manual, Architecture Document, and National Policy on Education documents
2. Real-time access to the e-Dossier Go backend API through various tools

Your role is to:
- Answer questions about e-Dossier functionality, workflows, and features using the knowledge base
- Help users navigate the system by querying live data from the Go backend
- Assist with administrative tasks like finding schools, personnel, students, sessions, etc.
- Provide insights from ML recommendations and reports
- Explain concepts from the National Policy on Education as they relate to e-Dossier
- Provide technical insights on system architecture, database design, and debugging

Guidelines:
- Always use the knowledge base (RAG) for questions about how e-Dossier works, policies, and procedures
- Use Go backend tools for real-time data queries (schools, students, personnel, reports, etc.)
- Combine both sources when appropriate (e.g., explain a concept from the manual, then show live data)
- Be concise but thorough
- If you don't know something, say so and offer to search the knowledge base or query the backend
- Format responses clearly with headings when appropriate

Available backend tools include:
- Authentication (login)
- Administrative hierarchy (states, zones, LGAs, schools)
- Personnel management
- Student management and enrollment
- Academic sessions and terms
- Results and report cards
- ML facility recommendations
- Reports and analytics (dashboard, zonal, gender, OSC)
- Attendance tracking

When users ask about specific data, use the appropriate tools to fetch real-time information.
When users ask about how to do something, consult the knowledge base first."""
        
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )
        
        self._message_histories: Dict[str, BaseChatMessageHistory] = {}
    
    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self._message_histories:
            self._message_histories[session_id] = RedisChatMessageHistory(
                session_id=session_id,
                url=settings.REDIS_URL,
                ttl=86400 * 7,
            )
        return self._message_histories[session_id]
    
    async def query_with_rag(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        try:
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENROUTER_API_KEY,
                openai_api_base=settings.OPENROUTER_BASE_URL,
            )
            query_embedding = await embeddings.aembed_query(query)
            
            results = await vector_store.similarity_search(query_embedding, k=k)
            
            return [
                {
                    "content": chunk.content,
                    "metadata": chunk.metadata.model_dump() if chunk.metadata else {},
                    "similarity": chunk.similarity,
                }
                for chunk in results
            ]
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return []
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        use_rag: bool = True,
        use_tools: bool = True,
    ) -> Dict[str, Any]:
        context_parts = []
        sources = []
        
        if use_rag:
            rag_results = await self.query_with_rag(message)
            if rag_results:
                context_parts.append("=== Knowledge Base Context ===")
                for i, result in enumerate(rag_results):
                    context_parts.append(f"\nSource {i+1} (similarity: {result['similarity']:.3f}):")
                    context_parts.append(result['content'][:1500])
                    sources.append({
                        "content": result['content'][:500],
                        "metadata": result['metadata'],
                        "similarity": result['similarity'],
                    })
        
        full_input = message
        if context_parts:
            full_input = "\n".join(context_parts) + "\n\n=== User Question ===\n" + message
        
        if use_tools:
            try:
                history = self._get_session_history(session_id)
                messages = history.messages + [HumanMessage(content=full_input)]
                
                result = await self.agent.ainvoke({"messages": messages})
                
                response_text = ""
                tool_calls = []
                tool_results = []
                
                for msg in result["messages"]:
                    if isinstance(msg, AIMessage):
                        if msg.tool_calls:
                            for tc in msg.tool_calls:
                                tool_calls.append({
                                    "name": tc["name"],
                                    "arguments": tc["args"],
                                    "id": tc["id"],
                                })
                        else:
                            response_text = msg.content
                    elif msg.type == "tool":
                        tool_results.append({
                            "tool_call_id": msg.tool_call_id,
                            "name": msg.name,
                            "content": str(msg.content)[:2000],
                            "success": True,
                        })
                
                return {
                    "message": response_text,
                    "tool_calls": tool_calls if tool_calls else None,
                    "tool_results": tool_results if tool_results else None,
                    "sources": sources if sources else None,
                }
            except Exception as e:
                logger.error(f"Agent execution error: {e}")
                err_str = str(e)
                if "Filter by Tool Compatibility" in err_str or "No endpoints found that support tool use" in err_str:
                    logger.warning("Model does not support tools or no tool endpoints available. Falling back to non-tool LLM execution...")
                    try:
                        response = await self.llm.ainvoke([
                            SystemMessage(content=self.system_prompt),
                            HumanMessage(content=full_input),
                        ])
                        return {
                            "message": response.content,
                            "tool_calls": None,
                            "tool_results": None,
                            "sources": sources if sources else None,
                        }
                    except Exception as fallback_err:
                        logger.error(f"Fallback execution error: {fallback_err}")
                return {
                    "message": f"I encountered an error while processing your request: {str(e)}",
                    "tool_calls": None,
                    "tool_results": None,
                    "sources": sources if sources else None,
                }
        else:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=full_input),
            ])
            return {
                "message": response.content,
                "tool_calls": None,
                "tool_results": None,
                "sources": sources if sources else None,
            }
    
    async def stream_message(
        self,
        message: str,
        session_id: str,
        use_rag: bool = True,
        use_tools: bool = True,
    ) -> AsyncGenerator[str, None]:
        """Stream the response token by token."""
        context_parts = []
        sources = []
        
        if use_rag:
            rag_results = await self.query_with_rag(message)
            if rag_results:
                context_parts.append("=== Knowledge Base Context ===")
                for i, result in enumerate(rag_results):
                    context_parts.append(f"\nSource {i+1} (similarity: {result['similarity']:.3f}):")
                    context_parts.append(result['content'][:1500])
                    sources.append({
                        "content": result['content'][:500],
                        "metadata": result['metadata'],
                        "similarity": result['similarity'],
                    })
        
        full_input = message
        if context_parts:
            full_input = "\n".join(context_parts) + "\n\n=== User Question ===\n" + message
        
        # First, yield sources if available
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        
        if use_tools:
            try:
                history = self._get_session_history(session_id)
                messages = history.messages + [HumanMessage(content=full_input)]
                
                # Stream from the agent
                async for chunk in self.agent.astream({"messages": messages}, stream_mode="messages"):
                    if chunk and isinstance(chunk[0], AIMessage):
                        content = chunk[0].content
                        if content:
                            yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"Streaming agent error: {e}")
                err_str = str(e)
                if "Filter by Tool Compatibility" in err_str or "No endpoints found that support tool use" in err_str:
                    logger.warning("Model does not support tools or no tool endpoints available. Streaming non-tool response...")
                    try:
                        async for chunk in self.llm.astream([
                            SystemMessage(content=self.system_prompt),
                            HumanMessage(content=full_input),
                        ]):
                            if chunk.content:
                                yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
                        return
                    except Exception as fallback_err:
                        yield f"data: {json.dumps({'type': 'error', 'error': str(fallback_err)})}\n\n"
                        return
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        else:
            try:
                async for chunk in self.llm.astream([
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=full_input),
                ]):
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"Streaming LLM error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


edossier_agent = EdossierAgent()