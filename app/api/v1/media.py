from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.user import User
from app.api.deps import get_current_user
from app.core.config import settings
import uuid
from supabase import create_client, Client

router = APIRouter()

def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a media file (avatar, workout image, etc.) to Supabase Storage.
    Returns the public URL for the file.
    """
    try:
        supabase = get_supabase()
        
        # Read file content
        file_bytes = await file.read()
        
        # Generate a unique path for the file: {user_id}/{uuid}_{filename}
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ""
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        storage_path = f"{current_user.id}/{unique_filename}"
        
        # Upload to 'media' bucket
        supabase.storage.from_("media").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        
        # Get the public URL
        public_url = supabase.storage.from_("media").get_public_url(storage_path)
        
        return {
            "status": "success",
            "url": public_url,
            "path": storage_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload media")

@router.delete("/{path:path}")
def delete_media(
    path: str,
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a media file from Supabase Storage.
    The path must start with the user's ID to prevent deleting others' files.
    """
    if not path.startswith(str(current_user.id)):
        raise HTTPException(status_code=403, detail="Cannot delete media owned by another user")
        
    try:
        supabase = get_supabase()
        res = supabase.storage.from_("media").remove([path])
        if not res:
            raise Exception("File not found or failed to delete")
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete media")
