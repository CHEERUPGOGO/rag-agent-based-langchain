"""
Chroma 向量数据库管理模块。
"""

import os
import shutil
from typing import Any, Dict, List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings

if settings.use_ollama_embeddings:
    from langchain_ollama import OllamaEmbeddings
else:
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings


class VectorStoreManager:
    """向量存储管理器。"""

    _instance = None
    _vectorstore = None
    _embeddings = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._embeddings is None:
            self._initialize_embeddings()
        if self._vectorstore is None:
            self._initialize_vectorstore()

    def _initialize_embeddings(self):
        if settings.use_ollama_embeddings:
            self._embeddings = OllamaEmbeddings(
                model=settings.ollama_embedding_model,
                base_url=settings.ollama_base_url,
            )
            print(f"Using Ollama embeddings: {settings.ollama_embedding_model}")
        else:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            print(f"Using HuggingFace embeddings: {settings.embedding_model}")

    def _initialize_vectorstore(self):
        os.makedirs(settings.chroma_persist_directory, exist_ok=True)
        self._vectorstore = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self._embeddings,
            persist_directory=settings.chroma_persist_directory,
        )

    @property
    def vectorstore(self) -> Chroma:
        return self._vectorstore

    @property
    def embeddings(self):
        return self._embeddings

    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        if ids is None:
            candidate_ids = [doc.metadata.get("chunk_id") for doc in documents]
            if all(candidate_ids):
                ids = candidate_ids
        return self._vectorstore.add_documents(documents=documents, ids=ids)

    def rebuild_from_documents(self, documents: List[Document]) -> None:
        if os.path.exists(settings.chroma_persist_directory):
            shutil.rmtree(settings.chroma_persist_directory, ignore_errors=True)
        self._initialize_vectorstore()
        if documents:
            ids = [doc.metadata.get("chunk_id") for doc in documents]
            self.add_documents(documents, ids=ids)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        return self._vectorstore.similarity_search(query, k=k, filter=filter)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[tuple]:
        return self._vectorstore.similarity_search_with_score(query, k=k, filter=filter)

    def delete_documents(self, ids: List[str]) -> None:
        self._vectorstore.delete(ids=ids)

    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            collection = self._vectorstore._collection
            return {
                "name": collection.name,
                "count": collection.count(),
            }
        except Exception:
            return {
                "name": settings.chroma_collection_name,
                "count": 0,
            }

    def as_retriever(self, search_kwargs: Optional[Dict] = None):
        if search_kwargs is None:
            search_kwargs = {"k": settings.retrieval_top_k}
        return self._vectorstore.as_retriever(search_kwargs=search_kwargs)


def get_vectorstore_manager() -> VectorStoreManager:
    return VectorStoreManager()