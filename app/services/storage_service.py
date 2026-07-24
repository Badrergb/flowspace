import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
from app.core.errors import safe_error_message

# Initialize boto3 S3 client for Cloudflare R2
s3_client = boto3.client(
    's3',
    endpoint_url=settings.R2_ENDPOINT_URL,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    region_name='auto'  # R2 requires region to be 'auto' or one of the valid regions
)

def upload_file_to_r2(bucket_name: str, file_path: str, file_bytes: bytes, content_type: str):
    # Using the bucket_name from R2_BUCKET_NAME if bucket_name parameter is generic, 
    # but we'll respect the passed bucket_name to keep the signature exactly the same.
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_path,
            Body=file_bytes,
            ContentType=content_type
        )
    except ClientError as e:
        safe_msg = safe_error_message(e, fallback="Failed to upload file to R2")
        raise Exception(safe_msg)
    
    return get_public_url(bucket_name, file_path)

def get_public_url(bucket_name: str, file_path: str) -> str:
    base_url = settings.R2_PUBLIC_URL_BASE.rstrip('/')
    return f"{base_url}/{file_path}"
