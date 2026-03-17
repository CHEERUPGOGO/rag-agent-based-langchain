"""
SQLite-backed repository for document metadata and chunk state.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.config import settings
from app.models.schemas import DocumentInfo


@dataclass
class DocumentRecord:
    """Persisted document metadata."""

    id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    upload_time: datetime
    status: str
    metadata: Dict[str, Any]


@dataclass
class DocumentChunkRecord:
    """Persisted chunk metadata and content."""

    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: Dict[str, Any]


class DocumentRepository:
    """Repository for document metadata and chunk content."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.metadata_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    upload_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
                """
            )

    def upsert_document(
        self,
        document: DocumentInfo,
        chunks: Iterable[DocumentChunkRecord],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents (
                    id, filename, file_type, file_size, chunk_count,
                    upload_time, status, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.filename,
                    document.file_type,
                    document.file_size,
                    document.chunk_count,
                    document.upload_time.isoformat(),
                    "indexed",
                    json.dumps(document.metadata, ensure_ascii=False),
                ),
            )
            conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document.id,))
            conn.executemany(
                """
                INSERT OR REPLACE INTO document_chunks (
                    chunk_id, document_id, chunk_index, content, metadata_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.chunk_index,
                        chunk.content,
                        json.dumps(chunk.metadata, ensure_ascii=False),
                    )
                    for chunk in chunks
                ],
            )

    def list_documents(self) -> List[DocumentInfo]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, filename, file_type, file_size, chunk_count,
                       upload_time, metadata_json
                FROM documents
                WHERE status = 'indexed'
                ORDER BY upload_time DESC
                """
            ).fetchall()
        return [self._row_to_document_info(row) for row in rows]

    def get_document(self, document_id: str) -> Optional[DocumentInfo]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, filename, file_type, file_size, chunk_count,
                       upload_time, metadata_json
                FROM documents
                WHERE id = ? AND status = 'indexed'
                """,
                (document_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_document_info(row)

    def list_chunk_records(self, document_id: Optional[str] = None) -> List[DocumentChunkRecord]:
        query = """
            SELECT chunk_id, document_id, chunk_index, content, metadata_json
            FROM document_chunks
        """
        params: tuple[Any, ...] = ()
        if document_id:
            query += " WHERE document_id = ?"
            params = (document_id,)
        query += " ORDER BY document_id, chunk_index"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_chunk_record(row) for row in rows]

    def delete_document(self, document_id: str) -> List[str]:
        chunk_ids = [chunk.chunk_id for chunk in self.list_chunk_records(document_id)]
        with self._connect() as conn:
            conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return chunk_ids

    def count_documents(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM documents WHERE status = 'indexed'"
            ).fetchone()
        return int(row["count"]) if row else 0

    def _row_to_document_info(self, row: sqlite3.Row) -> DocumentInfo:
        return DocumentInfo(
            id=row["id"],
            filename=row["filename"],
            file_type=row["file_type"],
            file_size=row["file_size"],
            chunk_count=row["chunk_count"],
            upload_time=datetime.fromisoformat(row["upload_time"]),
            metadata=json.loads(row["metadata_json"]),
        )

    def _row_to_chunk_record(self, row: sqlite3.Row) -> DocumentChunkRecord:
        return DocumentChunkRecord(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            metadata=json.loads(row["metadata_json"]),
        )
