"""
聊天路由模块 - 新增对话管理功能
"""

import json

from fastapi import APIRouter, HTTPException
from typing import Optional
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.services import get_chat_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])
chat_service = get_chat_service()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """与 Agent 进行非流式对话。"""
    try:
        result = await chat_service.chat(request)
        return ChatResponse(
            message=result["message"],
            conversation_id=result["conversation_id"],
            thoughts=result.get("thoughts"),
            sources=result.get("sources"),
            tokens_used=result.get("tokens_used"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """与 Agent 进行流式对话。"""

    async def event_generator():
        try:
            async for chunk in chat_service.stream_chat(request):
                event_type = chunk.get("type", "message")
                data = json.dumps(chunk, ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data}\n\n"
        except Exception as exc:
            error_data = json.dumps({"type": "error", "content": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# 【新增】对话管理端点
@router.get("/conversations")
async def list_conversations(user_id: Optional[str] = None, limit: int = 20):
    """获取对话列表"""
    conversations = await chat_service.list_conversations(user_id=user_id, limit=limit)
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str, user_id: Optional[str] = None):
    """获取特定对话的历史"""
    history = await chat_service.get_conversation_history(conversation_id, user_id=user_id)
    return {"conversation_id": conversation_id, "messages": history}


@router.get("/conversations/{conversation_id}/state")
async def get_conversation_state(conversation_id: str, user_id: Optional[str] = None):
    """获取对话的完整状态（LangGraph checkpoint）"""
    state = await chat_service.get_conversation_state(conversation_id, user_id=user_id)
    if state:
        # 从 checkpoint 中提取消息
        messages = state.get("values", {}).get("messages", [])
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "state": state.get("values", {}),
        }
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "state": {},
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: Optional[str] = None):
    """删除对话"""
    try:
        await chat_service.delete_conversation(conversation_id)
        return {"success": True, "message": f"对话 {conversation_id} 已删除"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "langchain-rag-agent"}
