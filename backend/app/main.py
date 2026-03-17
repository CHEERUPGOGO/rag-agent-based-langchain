"""
FastAPI main entry point for the LangChain RAG Agent backend.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import get_logger
from app.routers import chat_router, documents_router, evaluation_router

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LangChain RAG Agent service")
    logger.info("Vector database directory: %s", settings.chroma_persist_directory)
    logger.info("Active model: %s", settings.deepseek_model)

    yield

    logger.info("Shutting down LangChain RAG Agent service")


app = FastAPI(
    title="LangChain RAG Agent API",
    description="基于 LangChain 1.0 的全栈式 Agent 平台，支持 RAG 检索和联网搜索",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(evaluation_router)


@app.get("/")
async def root():
    return {
        "message": "欢迎使用 LangChain RAG Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/chat",
            "documents": "/api/documents",
            "evaluation": "/api/evaluation",
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "langchain-rag-agent",
    }


@app.get("/api/health")
async def api_health_check():
    return {
        "status": "healthy",
        "service": "langchain-rag-agent",
    }


@app.get("/api/config")
async def get_config():
    return {
        "model": settings.openrouter_model if (settings.default_provider == "openrouter" and settings.openrouter_api_key) else settings.deepseek_model,
        "embedding_model": settings.embedding_model,
        "retrieval_top_k": settings.retrieval_top_k,
        "rerank_top_k": settings.rerank_top_k,
    }