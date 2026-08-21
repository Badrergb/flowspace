import boto3
import logging
from app.core.errors import safe_error_message

logger = logging.getLogger(__name__)

MEDIA_BUCKET = "flowspace-media"


def upload_file_to_s3(file_path: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
    """
    Uploads a file to S3/R2 and returns the public URL.
    """
    try:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=MEDIA_BUCKET,
            Key=file_path,
            Body=file_bytes,
            ContentType=content_type,
        )
        url = f"https://{MEDIA_BUCKET}.s3.amazonaws.com/{file_path}"
        return url
    except Exception as e:
        safe_msg = safe_error_message(e, fallback="Failed to upload file to S3")
        logger.error(safe_msg)
        raise Exception(safe_msg)
