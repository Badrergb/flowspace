from supabase import create_client, Client
from app.core.config import settings
from app.core.errors import safe_error_message

# Initialize Supabase client for storage
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def upload_file_to_supabase(bucket_name: str, file_path: str, file_bytes: bytes, content_type: str) -> str:
    try:
        res = supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )
    except Exception as e:
        safe_msg = safe_error_message(e, fallback="Failed to upload file to Supabase")
        raise Exception(safe_msg)
    
    return get_public_url(bucket_name, file_path)

def get_public_url(bucket_name: str, file_path: str) -> str:
    return supabase.storage.from_(bucket_name).get_public_url(file_path)
