"""
Document service layer.
"""

from __future__ import annotations

import os
from typing import List

from fastapi import HTTPException, UploadFile
from langchain_core.documents import Document

from app.config import settings
from app.models.schemas import DocumentInfo, DocumentUploadResponse
from app.rag import DocumentProcessor, create_hybrid_retriever, get_vectorstore_manager
from app.repositories import DocumentChunkRecord, DocumentRepository


class DocumentService:
    """Coordinates persistence, vector indexing, and retriever rebuilds."""

    def __init__(self, repository: DocumentRepository | None = None):
        self.repository = repository or DocumentRepository()
        self.document_processor = DocumentProcessor()
        self.vectorstore_manager = get_vectorstore_manager()
        self.sync_vectorstore()

    def sync_vectorstore(self) -> None:
        """Rebuild Chroma from persisted chunk metadata to remove stale vectors."""
        self.vectorstore_manager.rebuild_from_documents(self.list_chunk_documents())

    async def upload_document(self, file: UploadFile) -> DocumentUploadResponse:
        if not self.document_processor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail=(
                    "不支持的文件类型。支持的类型: "
                    f"{list(self.document_processor.SUPPORTED_EXTENSIONS.keys())}"
                ),
            )

        content = await file.read()
        chunks, document_info = await self.document_processor.process_uploaded_file(
            file_content=content,
            filename=file.filename,
            upload_dir=settings.upload_directory,
        )
        chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks]
        self.vectorstore_manager.add_documents(chunks, ids=chunk_ids)
        self.repository.upsert_document(document_info, self._to_chunk_records(chunks))

        return DocumentUploadResponse(
            success=True,
            message=f"文档 '{file.filename}' 上传成功，已分割为 {len(chunks)} 个块",
            document=document_info,
        )

    async def upload_documents_batch(self, files: List[UploadFile]) -> dict:
        results = []
        for file in files:
            try:
                result = await self.upload_document(file)
                results.append(
                    {
                        "filename": file.filename,
                        "success": True,
                        "message": result.message,
                        "document_id": result.document.id if result.document else None,
                    }
                )
            except HTTPException as exc:
                results.append(
                    {
                        "filename": file.filename,
                        "success": False,
                        "message": str(exc.detail),
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "filename": file.filename,
                        "success": False,
                        "message": str(exc),
                    }
                )
        return {"results": results}

    def list_documents(self) -> List[DocumentInfo]:
        return self.repository.list_documents()

    def get_document(self, document_id: str) -> DocumentInfo:
        document = self.repository.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        return document

    def delete_document(self, document_id: str) -> dict:
        document = self.repository.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        chunk_ids = self.repository.delete_document(document_id)
        if chunk_ids:
            self.vectorstore_manager.delete_documents(chunk_ids)

        # 删除uploads目录中的物理文件
        stored_path = document.metadata.get("stored_path") if document.metadata else None
        if stored_path:
            if not os.path.isabs(stored_path):
                stored_path = os.path.join(settings.upload_directory, os.path.basename(stored_path))
            
            if os.path.exists(stored_path):
                try:
                    os.remove(stored_path)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"删除物理文件失败: {stored_path}, 错误: {e}")

        return {"success": True, "message": f"文档 {document_id} 已删除"}

    def get_stats(self) -> dict:
        stats = self.vectorstore_manager.get_collection_stats()
        chunk_count = len(self.repository.list_chunk_records())
        return {
            "total_documents": self.repository.count_documents(),
            "total_chunks": chunk_count,
            "collection_name": stats.get("name", "unknown"),
        }

    def build_retriever(self):
        return create_hybrid_retriever(documents=self.list_chunk_documents())

    def list_chunk_documents(self) -> List[Document]:
        chunk_records = self.repository.list_chunk_records()
        return [
            Document(page_content=chunk.content, metadata=chunk.metadata)
            for chunk in chunk_records
        ]

    def _to_chunk_records(self, chunks: List[Document]) -> List[DocumentChunkRecord]:
        records: List[DocumentChunkRecord] = []
        for chunk in chunks:
            records.append(
                DocumentChunkRecord(
                    chunk_id=chunk.metadata["chunk_id"],
                    document_id=chunk.metadata["doc_id"],
                    chunk_index=chunk.metadata["chunk_index"],
                    content=chunk.page_content,
                    metadata=chunk.metadata,
                )
            )
        return records


_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service