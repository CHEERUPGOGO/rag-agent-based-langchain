"""
Pydantic 数据模型定义
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    conversation_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    use_rag: bool = Field(True, description="是否使用RAG检索")
    use_web_search: bool = Field(True, description="是否使用联网搜索")
    stream: bool = Field(True, description="是否流式返回")


class AgentThought(BaseModel):
    """Agent思考过程模型"""
    step: int = Field(..., description="步骤序号")
    action: str = Field(..., description="执行的动作")
    action_input: Optional[str] = Field(None, description="动作输入")
    observation: Optional[str] = Field(None, description="观察结果")
    thought: Optional[str] = Field(None, description="思考内容")


class SearchResult(BaseModel):
    """搜索结果模型"""
    source: str = Field(..., description="来源类型: rag/web")
    content: str = Field(..., description="内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    score: Optional[float] = Field(None, description="相关性分数")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: str = Field(..., description="回复内容")
    conversation_id: str = Field(..., description="会话ID")
    thoughts: Optional[List[AgentThought]] = Field(None, description="思考过程")
    sources: Optional[List[SearchResult]] = Field(None, description="引用来源")
    tokens_used: Optional[int] = Field(None, description="消耗的token数量")


class DocumentInfo(BaseModel):
    """文档信息模型"""
    id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小(字节)")
    chunk_count: int = Field(..., description="分块数量")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class DocumentUploadResponse(BaseModel):
    """文档上传响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    document: Optional[DocumentInfo] = Field(None, description="文档信息")


class EvaluationSample(BaseModel):
    """评估样本模型"""
    question: str = Field(..., description="问题")
    answer: str = Field(..., description="回答")
    contexts: List[str] = Field(..., description="上下文列表")
    ground_truth: Optional[str] = Field(None, description="标准答案")


class EvaluationRequest(BaseModel):
    """评估请求模型"""
    samples: List[EvaluationSample] = Field(..., description="评估样本列表")
    metrics: Optional[List[str]] = Field(
        default=["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
        description="评估指标"
    )


class EvaluationMetrics(BaseModel):
    """评估指标结果"""
    faithfulness: Optional[float] = Field(None, description="忠实度")
    answer_relevancy: Optional[float] = Field(None, description="答案相关性")
    context_precision: Optional[float] = Field(None, description="上下文精确度")
    context_recall: Optional[float] = Field(None, description="上下文召回率")


class EvaluationResponse(BaseModel):
    """评估响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    metrics: Optional[EvaluationMetrics] = Field(None, description="评估指标")
    details: Optional[List[Dict[str, Any]]] = Field(None, description="详细结果")
