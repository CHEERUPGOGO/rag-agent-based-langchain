"""
LangChain 1.0 Agent 核心模块。
"""

import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import create_react_agent as create_agent

from app.config import settings
from app.models.schemas import AgentThought, ChatMessage, SearchResult
from app.conversation import get_checkpoint_manager
from .prompts import AGENT_SYSTEM_PROMPT
from .tools import get_all_tools, set_retriever


class AgentExecutor:
    """Agent 执行器。"""

    def __init__(self, retriever=None):
        if retriever:
            set_retriever(retriever)

        if settings.default_provider == "openrouter" and settings.openrouter_api_key:
            self.llm = ChatOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                model=settings.openrouter_model,
                temperature=0.7,
                streaming=True,
                timeout=30,
                max_retries=3,
            )
        else:
            self.llm = ChatOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
                temperature=0.7,
                streaming=True,
            )

        self.tools = get_all_tools(include_rag=True, include_web=True)
        self.checkpoint_manager = get_checkpoint_manager(settings.checkpoint_db_path)
        self.db_path = settings.checkpoint_db_path
        
        self.trimmer = trim_messages(
              max_tokens=20,                # 普通消息最多20条
              strategy="last",              # 保留最新
              token_counter=len,            # 按消息条数计数
              allow_partial=False    
        )

    def set_retriever(self, retriever) -> None:
        set_retriever(retriever)

    def _convert_history_to_messages(self, history: List[Dict]) -> List[Any]:
        """转换历史消息为 LangChain 消息格式。"""
        messages = []
        for msg in history:
            role = msg.get("role") if isinstance(msg, dict) else msg.role
            content = msg.get("content") if isinstance(msg, dict) else msg.content
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        
        return messages

    def _get_agent(self, checkpointer, use_rag: bool = True, use_web_search: bool = True):
        """创建智能体。"""
        return create_agent(
            model=self.llm,
            tools=get_all_tools(include_rag=use_rag, include_web=use_web_search),
            checkpointer=checkpointer,
        )

    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        use_rag: bool = True,
        use_web_search: bool = True,
    ) -> Dict[str, Any]:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        config = {"configurable": {"thread_id": conversation_id}}
        thoughts: List[AgentThought] = []
        sources: List[SearchResult] = []
        final_response = ""

        try:
            async with AsyncSqliteSaver.from_conn_string(self.db_path) as saver:
                agent = self._get_agent(saver, use_rag, use_web_search)
                
                # 获取当前状态，判断是否需要注入 SystemMessage
                state = await agent.aget_state(config)
                messages = []
                
                # 如果没有历史状态，注入系统提示词和可能的历史消息
                if not state.values or "messages" not in state.values:
                    messages.append(SystemMessage(
                        content=AGENT_SYSTEM_PROMPT.format(
                            chat_history="",
                            input=message,
                            agent_scratchpad="",
                        )
                    ))
                    if history:
                        messages.extend(self._convert_history_to_messages(history))
                else:
                    messages.extend(state.values["messages"])
                
                # 添加当前用户消息
                messages.append(HumanMessage(content=message))
                
                # 持久化用户消息
                await self.checkpoint_manager.add_message(conversation_id, "user", message, user_id=user_id)

                system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
                normal_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
                trimmed_normal_msgs = self.trimmer.invoke(normal_msgs)
                trimmed_messages = system_msgs + trimmed_normal_msgs

                result = await agent.ainvoke({"messages": trimmed_messages}, config=config)
                
                final_state = await agent.aget_state(config)
                if final_state.values and "messages" in final_state.values:
                    # 提取工具调用和来源（从final_state读取，而非result）
                    for msg in final_state.values["messages"]:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                thoughts.append(
                                    AgentThought(
                                        step=len(thoughts) + 1,
                                        action=tool_call.get("name", "unknown"),
                                        action_input=str(tool_call.get("args", {})),
                                        observation=None,
                                        thought="执行工具调用",
                                    )
                                )
                        
                        if hasattr(msg, "name") and msg.name in ["rag_search_tool", "web_search_tool"]:
                            source_type = "rag" if msg.name == "rag_search_tool" else "web"
                            sources.append(
                                SearchResult(
                                    source=source_type,
                                    content=msg.content[:500] if msg.content else "",
                                    metadata={"tool": msg.name},
                                )
                            )
                            if thoughts:
                                thoughts[-1].observation = msg.content[:200]
                    
                    # 提取AI响应（从final_state读取，保证是裁剪后的最新消息）
                    last_msg = final_state.values["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        final_response = last_msg.content
                        # 持久化 AI 响应
                        await self.checkpoint_manager.add_message(conversation_id, "assistant", final_response, user_id=user_id)

                return {
                    "message": final_response,
                    "conversation_id": conversation_id,
                    "thoughts": thoughts,
                    "sources": sources,
                    "tokens_used": None,
                }
        except Exception as exc:
            error_msg = str(exc)
            if "Authentication" in error_msg or "governor" in error_msg:
                error_msg = "API 认证失败，请检查 API 密钥配置。"
            else:
                error_msg = f"处理请求时发生错误: {error_msg}"
            return {
                "message": error_msg,
                "conversation_id": conversation_id,
                "thoughts": [],
                "sources": [],
                "tokens_used": None,
            }

    async def stream_chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        use_rag: bool = True,
        use_web_search: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        config = {"configurable": {"thread_id": conversation_id}}
        thoughts: List[AgentThought] = []
        sources: List[SearchResult] = []

        try:
            async with AsyncSqliteSaver.from_conn_string(self.db_path) as saver:
                agent = self._get_agent(saver, use_rag, use_web_search)
                
                # 获取当前状态，判断是否需要注入 SystemMessage
                state = await agent.aget_state(config)
                messages = []
                
                # 如果没有历史状态，注入系统提示词和可能的历史消息
                if not state.values or "messages" not in state.values:
                    messages.append(SystemMessage(
                        content=AGENT_SYSTEM_PROMPT.format(
                            chat_history="",
                            input=message,
                            agent_scratchpad="",
                        )
                    ))
                    if history:
                        messages.extend(self._convert_history_to_messages(history))
                else:
                    messages.extend(state.values["messages"])
                
                # 添加当前用户消息
                messages.append(HumanMessage(content=message))
                
                # 持久化用户消息
                await self.checkpoint_manager.add_message(conversation_id, "user", message, user_id=user_id)
                
                system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
                normal_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
                trimmed_normal_msgs = self.trimmer.invoke(normal_msgs)
                trimmed_messages = system_msgs + trimmed_normal_msgs

                full_response = ""

                async for event in agent.astream_events(
                    {"messages": trimmed_messages},
                    config=config,
                    version="v2",
                ):
                    kind = event.get("event", "")

                    if kind == "on_chat_model_stream":
                        content = event.get("data", {}).get("chunk", {})
                        if hasattr(content, "content") and content.content:
                            full_response += content.content
                            yield {
                                "type": "token",
                                "content": content.content,
                                "conversation_id": conversation_id,
                            }

                    elif kind == "on_tool_start":
                        tool_name = event.get("name", "unknown")
                        tool_input = event.get("data", {}).get("input", {})
                        thoughts.append(
                            AgentThought(
                                step=len(thoughts) + 1,
                                action=tool_name,
                                action_input=str(tool_input),
                                thought="正在执行工具...",
                            )
                        )
                        yield {
                            "type": "thought",
                            "content": thoughts[-1].model_dump(),
                            "conversation_id": conversation_id,
                        }

                    elif kind == "on_tool_end":
                        output = event.get("data", {}).get("output", "")
                        if thoughts:
                            thoughts[-1].observation = str(output)[:200]

                        tool_name = event.get("name", "")
                        if tool_name == "rag_search_tool":
                            source_type = "rag"
                        elif tool_name == "web_search_tool":
                            source_type = "web"
                        else:
                            source_type = "unknown"

                        sources.append(
                            SearchResult(
                                source=source_type,
                                content=str(output)[:500],
                                metadata={"tool": tool_name},
                            )
                        )
                        yield {
                            "type": "source",
                            "content": sources[-1].model_dump(),
                            "conversation_id": conversation_id,
                        }

                # 持久化 AI 响应
                if full_response:
                    await self.checkpoint_manager.add_message(conversation_id, "assistant", full_response, user_id=user_id)

                yield {
                    "type": "done",
                    "conversation_id": conversation_id,
                    "thoughts": [thought.model_dump() for thought in thoughts],
                    "sources": [source.model_dump() for source in sources],
                }
        except Exception as exc:
            error_msg = str(exc)
            if "Authentication" in error_msg or "governor" in error_msg:
                error_msg = "API 认证失败，请检查 API 密钥配置。"
            yield {
                "type": "error",
                "content": error_msg,
                "conversation_id": conversation_id,
            }


def create_rag_agent(retriever=None) -> AgentExecutor:
    return AgentExecutor(retriever=retriever)