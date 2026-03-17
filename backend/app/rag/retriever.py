"""
混合检索器模块。
实现基于 RRF 的向量检索 + BM25 融合。
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from app.config import settings
from .vectorstore import get_vectorstore_manager


class HybridRetriever(BaseRetriever):
    """向量检索与 BM25 的混合检索器。"""

    vectorstore_retriever: Any = Field(default=None, description="向量存储检索器")
    bm25_retriever: Any = Field(default=None, description="BM25 检索器")
    k: int = Field(default=5, description="返回结果数量")
    rrf_k: int = Field(default=60, description="RRF 参数")
    vector_weight: float = Field(default=0.5, description="向量检索权重")
    bm25_weight: float = Field(default=0.5, description="BM25 检索权重")
    documents: List[Document] = Field(default_factory=list, description="文档列表")

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        documents: Optional[List[Document]] = None,
        k: int = 5,
        rrf_k: int = 60,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.k = k
        self.rrf_k = rrf_k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.documents = documents or []

        vectorstore_manager = get_vectorstore_manager()
        self.vectorstore_retriever = vectorstore_manager.as_retriever(
            search_kwargs={"k": k * 2}
        )
        if self.documents:
            self._init_bm25_retriever()

    def _init_bm25_retriever(self):
        if self.documents:
            self.bm25_retriever = BM25Retriever.from_documents(self.documents, k=self.k * 2)

    def _reciprocal_rank_fusion(
        self,
        results_list: List[List[Document]],
        weights: List[float],
    ) -> List[Document]:
        doc_scores: Dict[int, float] = defaultdict(float)
        doc_map: Dict[int, Document] = {}

        for results, weight in zip(results_list, weights):
            for rank, doc in enumerate(results):
                doc_id = hash((doc.page_content, doc.metadata.get("chunk_id")))
                doc_scores[doc_id] += weight / (self.rrf_k + rank + 1)
                if doc_id not in doc_map:
                    doc_map[doc_id] = doc

        sorted_doc_ids = sorted(doc_scores.keys(), key=lambda item: doc_scores[item], reverse=True)
        fused_docs: List[Document] = []
        for doc_id in sorted_doc_ids[:self.k]:
            doc = doc_map[doc_id]
            doc.metadata["rrf_score"] = doc_scores[doc_id]
            fused_docs.append(doc)
        return fused_docs

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        results_list: List[List[Document]] = []
        weights: List[float] = []

        try:
            vector_results = self.vectorstore_retriever.invoke(query)
            if vector_results:
                results_list.append(vector_results)
                weights.append(self.vector_weight)
        except Exception as exc:
            print(f"向量检索失败: {exc}")

        if self.bm25_retriever:
            try:
                bm25_results = self.bm25_retriever.invoke(query)
                if bm25_results:
                    results_list.append(bm25_results)
                    weights.append(self.bm25_weight)
            except Exception as exc:
                print(f"BM25 检索失败: {exc}")

        if not results_list:
            return []
        if len(results_list) == 1:
            return results_list[0][:self.k]
        return self._reciprocal_rank_fusion(results_list, weights)


def create_hybrid_retriever(
    documents: Optional[List[Document]] = None,
    k: int = None,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
) -> HybridRetriever:
    if k is None:
        k = settings.rerank_top_k
    return HybridRetriever(
        documents=documents,
        k=k,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
    )
