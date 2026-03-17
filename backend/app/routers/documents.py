"""
文档管理路由模块。
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import DocumentInfo, DocumentUploadResponse
from app.services import get_document_service

router = APIRouter(prefix="/api/documents", tags=["Documents"])
document_service = get_document_service()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        return await document_service.upload_document(file)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/upload/batch")
async def upload_documents_batch(files: list[UploadFile] = File(...)):
    return await document_service.upload_documents_batch(files)


@router.get("/", response_model=list[DocumentInfo])
async def list_documents():
    return document_service.list_documents()


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    return document_service.get_document(document_id)


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    try:
        return document_service.delete_document(document_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/stats/overview")
async def get_stats():
    return document_service.get_stats()
