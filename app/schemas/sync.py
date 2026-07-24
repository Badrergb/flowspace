from typing import List, Optional, Any, Dict
from pydantic import BaseModel, UUID4
from datetime import datetime

class SyncOperationSchema(BaseModel):
    operation_id: UUID4 # Used for idempotency
    entity_type: str
    entity_id: UUID4
    operation_type: str
    payload: Optional[Dict[str, Any]] = None

class SyncUploadRequest(BaseModel):
    device_id: UUID4
    operations: List[SyncOperationSchema]

class SyncUploadResponse(BaseModel):
    status: str
    processed_count: int
    version: int

class SyncDownloadRequest(BaseModel):
    device_id: UUID4
    last_sync_version: int

class SyncOperationResponse(BaseModel):
    id: UUID4
    entity_type: str
    entity_id: UUID4
    operation_type: str
    payload: Optional[Dict[str, Any]] = None
    version: int
    
    model_config = {"from_attributes": True}

class SyncDownloadResponse(BaseModel):
    operations: List[SyncOperationResponse]
    new_last_sync_version: int
