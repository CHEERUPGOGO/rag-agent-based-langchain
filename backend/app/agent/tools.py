"""
Agent 工具定义。
包含 RAG 检索工具和 Tavily 联网搜索工具。
"""

import concurrent.futures
from typing import List, Literal

from langchain_core.tools import Tool, tool
from tavily import TavilyClient

from app.config import settings


_retriever = None


def set_retriever(retriever):
    """设置 RAG 检索器。"""
    global _retriever
    _retriever = retriever


def get_retriever():
    """获取 RAG 检索器。"""
    return _retriever


@tool
def rag_search_tool(query: str) -> str:
    """从本地知识库中检索相关信息。"""
    retriever = get_retriever()
    if retriever is None:
        return "知识库未初始化或暂无文档"

    try:
        docs = retriever.invoke(query)
        if not docs:
            return "未找到相关文档"

        results = []
        for index, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "未知来源")
            content = doc.page_content[:500]
            results.append(f"[{index}] 来源: {source}\n内容: {content}")
        return "\n\n".join(results)
    except Exception as exc:
        return f"检索时发生错误: {exc}"


@tool("web_search_tool")
def web_search_tool(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search."""
    try:
        if not settings.tavily_api_key:
            return "错误: 未配置 Tavily API 密钥"

        tavily_client = TavilyClient(api_key=settings.tavily_api_key)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                tavily_client.search,
                query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic,
            )
            results = future.result(timeout=15)

        if isinstance(results, str):
            return results

        if isinstance(results, dict) and "results" in results:
            formatted_results = []
            for index, result in enumerate(results["results"], start=1):
                title = result.get("title", "无标题")
                content = result.get("content", "")[:300]
                url = result.get("url", "")
                formatted_results.append(f"[{index}] {title}\n{content}\n链接: {url}")
            return "\n\n".join(formatted_results) if formatted_results else "未找到相关结果"

        return str(results)
    except concurrent.futures.TimeoutError:
        return "联网搜索超时，请稍后重试。"
    except Exception as exc:
        print(f"Tavily 搜索错误详情: {exc}")
        return f"联网搜索时发生错误: {exc}"


def get_all_tools(include_rag: bool = True, include_web: bool = True) -> List[Tool]:
    tools = []
    if include_rag:
        tools.append(rag_search_tool)
    if include_web:
        tools.append(web_search_tool)
    return tools


internet_search = web_search_tool
