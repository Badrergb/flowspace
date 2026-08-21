from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from google.cloud.firestore_v1 import Client as FirestoreClient
from app.db.database import get_db
from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.config import settings
import boto3
import hashlib
import base64
import io
import json
from cryptography.fernet import Fernet

router = APIRouter()


def get_encryption_key() -> bytes:
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


@router.post("/create")
@limiter.limit("5/minute")
async def create_backup(
    request: Request,
    file: UploadFile = File(...),
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Encrypts the user's backup file and stores it to S3/R2."""
    uid = current_user["uid"]
    try:
        content = await file.read()
        fernet = Fernet(get_encryption_key())
        encrypted_content = fernet.encrypt(content)

        s3 = boto3.client("s3")
        file_path = f"{uid}/{file.filename}.enc"
        s3.put_object(Bucket="flowspace-backups", Key=file_path, Body=encrypted_content)

        return {"status": "success", "message": "Backup uploaded and encrypted successfully.", "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process backup")


@router.get("/list")
@limiter.limit("10/minute")
def list_backups(
    request: Request,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    try:
        s3 = boto3.client("s3")
        res = s3.list_objects_v2(Bucket="flowspace-backups", Prefix=f"{uid}/")
        files = [obj["Key"] for obj in res.get("Contents", [])]
        return {"backups": files}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list backups")


@router.post("/restore")
@limiter.limit("5/minute")
def restore_backup(
    request: Request,
    backup_path: str,
    db: FirestoreClient = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    if not backup_path.startswith(uid):
        raise HTTPException(status_code=403, detail="Access denied to this backup")

    try:
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket="flowspace-backups", Key=backup_path)
        encrypted_content = obj["Body"].read()

        fernet = Fernet(get_encryption_key())
        decrypted_content = fernet.decrypt(encrypted_content)

        return {"status": "success", "message": "Backup ready for download.", "size": len(decrypted_content)}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve backup")
