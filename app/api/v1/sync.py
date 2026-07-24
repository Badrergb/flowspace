from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.sync import SyncUploadRequest, SyncUploadResponse, SyncDownloadRequest, SyncDownloadResponse
from app.api.deps import get_current_user
from app.services.sync_service import SyncService
from app.core.rate_limit import limiter

router = APIRouter()

@router.post("/upload", response_model=SyncUploadResponse)
@limiter.limit("30/minute")
def sync_upload(
    request: Request,
    payload: SyncUploadRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Receives local operations from a device and applies them (LWW conflict resolution).
    """
    sync_service = SyncService(db)
    result = sync_service.process_upload(current_user.id, payload.device_id, payload.operations)
    return result

@router.post("/download", response_model=SyncDownloadResponse)
@limiter.limit("30/minute")
def sync_download(
    request: Request,
    payload: SyncDownloadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns operations that occurred after the given version, excluding operations from this device.
    """
    sync_service = SyncService(db)
    result = sync_service.get_downloads(current_user.id, payload.device_id, payload.last_sync_version)
    return result
