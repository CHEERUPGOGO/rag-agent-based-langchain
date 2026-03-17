"""
Chat service layer - AsyncSqliteSaver 版本
"""

from __future__ import annotations

from typing import AsyncGenerator, Any, Dict, List, Optional

from app.agent import AgentExecutor, create_rag_agent
from app.models.schemas import ChatRequest
from app.services.document_service import get_document_service
from app.conversation.checkpoint_manager import get_checkpoint_manager


class ChatService:
    """Wraps agent access and keeps retriever state fresh."""

    def __init__(self):
        self._agent: AgentExecutor | None = None
        self.checkpoint_manager = get_checkpoint_manager()

    def _get_agent(self) -> AgentExecutor:
        if self._agent is None:
            self._agent = create_rag_agent()
        return self._agent

    async def chat(self, request: ChatRequest) -> dict:
        agent = self._get_agent()
        agent.set_retriever(get_document_service().build_retriever())
        
        return await agent.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            use_rag=request.use_rag,
            use_web_search=request.use_web_search,
        )

    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[dict, None]:
        agent = self._get_agent()
        agent.set_retriever(get_document_service().build_retriever())
        
        async for chunk in agent.stream_chat(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            use_rag=request.use_rag,
            use_web_search=request.use_web_search,
        ):
            yield chunk

    async def get_conversation_history(self, conversation_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return await self.checkpoint_manager.get_conversation_history(conversation_id)

    async def get_conversation_state(self, conversation_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取对话的完整状态（包括 LangGraph checkpoint）"""
        return await self.checkpoint_manager.get_conversation_state(conversation_id)

    async def get_all_checkpoints(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话的所有版本/检查点"""
        return await self.checkpoint_manager.get_all_checkpoints(conversation_id)

    async def list_conversations(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """列出对话列表"""
        return await self.checkpoint_manager.list_conversations(user_id, limit)

    async def delete_conversation(self, conversation_id: str) -> None:
        """删除对话"""
        await self.checkpoint_manager.delete_conversation(conversation_id)


_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
