from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.config import settings
from cryptography.fernet import Fernet
import hashlib
import base64
from supabase import create_client, Client
import io

router = APIRouter()

def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def get_encryption_key() -> bytes:
    # Derive a 32-byte urlsafe-base64 key from SECRET_KEY
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)

@router.post("/create")
@limiter.limit("5/minute")
async def create_backup(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Encrypts the provided database backup using a server-managed key and uploads it.
    """
    try:
        content = await file.read()
        fernet = Fernet(get_encryption_key())
        encrypted_content = fernet.encrypt(content)
        
        supabase = get_supabase()
        file_path = f"{current_user.id}/{file.filename}.enc"
        
        res = supabase.storage.from_("backups").upload(
            file=encrypted_content,
            path=file_path,
            file_options={"content-type": "application/octet-stream"}
        )
        
        return {"status": "success", "message": "Backup uploaded and encrypted successfully.", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process backup")

@router.get("/list")
@limiter.limit("10/minute")
def list_backups(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists available backups for the user.
    """
    try:
        supabase = get_supabase()
        res = supabase.storage.from_("backups").list(f"{current_user.id}/")
        
        return {"backups": res if isinstance(res, list) else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list backups")

@router.post("/restore")
@limiter.limit("5/minute")
def restore_backup(
    request: Request,
    backup_path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Decrypts and returns the requested backup.
    """
    if not backup_path.startswith(str(current_user.id)):
        raise HTTPException(status_code=403, detail="Access denied to this backup")
        
    try:
        supabase = get_supabase()
        res = supabase.storage.from_("backups").download(backup_path)
        
        fernet = Fernet(get_encryption_key())
        decrypted_content = fernet.decrypt(res)
        
        # In a real app, you would return this as a StreamingResponse
        # For MVP, we return a success payload (or a link)
        return {"status": "success", "message": "Backup ready for download.", "size": len(decrypted_content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve backup")
