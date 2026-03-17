"""
文档处理模块
支持多种文档格式的解析和分块
"""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.schemas import DocumentInfo


class DocumentProcessor:
    """文档处理器。"""

    SUPPORTED_EXTENSIONS = {
        ".pdf": PyPDFLoader,
        ".docx": Docx2txtLoader,
        ".doc": Docx2txtLoader,
        ".txt": TextLoader,
        ".md": UnstructuredMarkdownLoader,
    }

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", ".", " ", ""]
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def is_supported(self, filename: str) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.SUPPORTED_EXTENSIONS

    def get_loader(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        loader_class = self.SUPPORTED_EXTENSIONS.get(ext)
        if loader_class is None:
            raise ValueError(f"不支持的文件类型: {ext}")
        return loader_class(file_path)

    def load_and_split(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        loader = self.get_loader(file_path)
        documents = loader.load()

        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)

        chunks = self.text_splitter.split_documents(documents)
        doc_id = metadata.get("doc_id", "unknown") if metadata else "unknown"
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{doc_id}:{index}"
            chunk.metadata["chunk_index"] = index
        return chunks

    async def process_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        upload_dir: str = "./uploads",
    ) -> tuple[List[Document], DocumentInfo]:
        os.makedirs(upload_dir, exist_ok=True)

        doc_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1]
        saved_filename = f"{doc_id}{ext}"
        file_path = os.path.join(upload_dir, saved_filename)

        with open(file_path, "wb") as file_handle:
            file_handle.write(file_content)

        try:
            metadata = {
                "doc_id": doc_id,
                "source": filename,
                "file_type": ext.lstrip("."),
                "upload_time": datetime.now().isoformat(),
                "stored_path": file_path,
            }
            chunks = self.load_and_split(file_path, metadata)
            doc_info = DocumentInfo(
                id=doc_id,
                filename=filename,
                file_type=ext.lstrip("."),
                file_size=len(file_content),
                chunk_count=len(chunks),
                upload_time=datetime.now(),
                metadata=metadata,
            )
            return chunks, doc_info
        except Exception:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    def split_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        chunks = self.text_splitter.split_text(text)
        documents = []
        prefix = metadata.get("doc_id", "text") if metadata else "text"
        for index, chunk in enumerate(chunks):
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata["chunk_id"] = f"{prefix}:{index}"
            doc_metadata["chunk_index"] = index
            documents.append(Document(page_content=chunk, metadata=doc_metadata))
        return documents


_document_processor = None


def get_document_processor() -> DocumentProcessor:
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor
