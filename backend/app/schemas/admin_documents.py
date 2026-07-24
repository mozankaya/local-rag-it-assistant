from typing import Optional

from pydantic import BaseModel


class AdminDocumentResponse(BaseModel):
    document_id: str
    title: str
    category: Optional[str] = None
    file_type: Optional[str] = None
    source_file_name: Optional[str] = None
    last_updated: Optional[str] = None
    chunk_count: int


class PaginatedAdminDocumentsResponse(BaseModel):
    items: list[AdminDocumentResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class DocumentCategoryResponse(BaseModel):
    category: str
    document_count: int
    
    
class ReindexResponse(BaseModel):
    success: bool
    message: str
    

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    file_name: str
    category: str
    source_path: str