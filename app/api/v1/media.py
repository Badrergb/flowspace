from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.api.deps import get_current_user
import uuid
import boto3
from botocore.exceptions import ClientError

router = APIRouter()


def get_s3():
    return boto3.client("s3")


MEDIA_BUCKET = "flowspace-media"


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Uploads a media file (avatar, workout image, etc.) to S3/R2.
    Returns the public URL for the file.
    """
    uid = current_user["uid"]
    try:
        file_bytes = await file.read()
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        storage_path = f"{uid}/{unique_filename}"

        s3 = get_s3()
        s3.put_object(
            Bucket=MEDIA_BUCKET,
            Key=storage_path,
            Body=file_bytes,
            ContentType=file.content_type or "application/octet-stream",
        )

        url = f"https://{MEDIA_BUCKET}.s3.amazonaws.com/{storage_path}"
        return {"status": "success", "url": url, "path": storage_path}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload media")


@router.delete("/{path:path}")
def delete_media(
    path: str,
    current_user: dict = Depends(get_current_user),
):
    """Deletes a media file from S3/R2. Path must start with the user's UID."""
    uid = current_user["uid"]
    if not path.startswith(uid):
        raise HTTPException(status_code=403, detail="Cannot delete media owned by another user")

    try:
        s3 = get_s3()
        s3.delete_object(Bucket=MEDIA_BUCKET, Key=path)
        return {"status": "success"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete media")
