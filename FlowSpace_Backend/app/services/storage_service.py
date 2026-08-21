import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

# Initialize boto3 S3 client for Cloudflare R2
s3_client = boto3.client(
    's3',
    endpoint_url=settings.R2_ENDPOINT_URL,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    region_name='auto'  # R2 requires region to be 'auto' or one of the valid regions
)

def upload_file_to_supabase(bucket_name: str, file_path: str, file_bytes: bytes, content_type: str):
    # Using the bucket_name from R2_BUCKET_NAME if bucket_name parameter is generic, 
    # but we'll respect the passed bucket_name to keep the signature exactly the same.
    # Usually we use the configured bucket name if there's only one, but we'll use the param.
    # Actually, R2_BUCKET_NAME is in settings, but we should probably use it or the passed one.
    # Let's use the passed one to preserve logic perfectly.
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_path,
            Body=file_bytes,
            ContentType=content_type
        )
    except ClientError as e:
        raise Exception(f"Failed to upload file to R2: {str(e)}")
    
    return get_public_url(bucket_name, file_path)

def get_public_url(bucket_name: str, file_path: str) -> str:
    # Construct the public URL assuming the bucket is configured for public access.
    # Note: R2 custom domains or r2.dev domain should ideally be used.
    # We will just construct a standard path-style or virtual-hosted style URL.
    # For R2 public buckets, it's typically https://pub-<id>.r2.dev/file_path
    # Since we don't have the public domain configured in settings, we can use the endpoint_url 
    # or just format it as endpoint_url/bucket_name/file_path for an S3-compatible path.
    # If endpoint URL is https://<account-id>.r2.cloudflarestorage.com
    # we can return endpoint_url/bucket_name/file_path.
    base_url = settings.R2_ENDPOINT_URL.rstrip('/')
    return f"{base_url}/{bucket_name}/{file_path}"
