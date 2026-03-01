import boto3
from botocore.exceptions import ClientError
from app.utils.settings import settings
import uuid
import logging

logger = logging.getLogger(__name__)

_s3_client = boto3.client("s3",
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                          region_name=settings.AWS_REGION,)

_MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024 
_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def validate_image(name: str, size: int | None = None) -> bool:
    if "." not in name:
        logger.warning(f"File has no extension: {name}")
        return False
    file_ext = name.lower().rsplit(".", 1)[-1] 
    if file_ext not in _ALLOWED_EXTENSIONS:
        logger.warning(f"Rejected file extension: {file_ext}")
        return False
    if size is not None and size > _MAX_IMAGE_SIZE_BYTES:
        logger.warning(f"File too large: {size} bytes (max {_MAX_IMAGE_SIZE_BYTES})")
        return False
    return True

def s3_upload(content: bytes, name: str, content_type: str) -> str | None:
    if len(content) > _MAX_IMAGE_SIZE_BYTES:
        logger.error(f"s3_upload called with oversized content: {len(content)} bytes")
        return None
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    unique_name = f"profile_images/{uuid.uuid4()}.{ext}"
    try:
        _s3_client.put_object(Bucket=settings.S3_BUCKET_NAME,
                              Key=unique_name,
                              Body=content,
                              ContentType=content_type,)
        s3_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_name}"
        logger.info(f"Uploaded to S3: {unique_name}")
        return s3_url
    except ClientError as e:
        logger.error(f"S3 upload failed: {e.response['Error']['Code']} — {e.response['Error']['Message']}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during S3 upload: {e}")
        return None

def s3_delete(url: str) -> bool:
    expected_prefix = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/"
    if not url.startswith(expected_prefix):
        logger.error(f"s3_delete received a URL that doesn't match expected S3 format. "f"Expected prefix: {expected_prefix} — Got: {url[:80]}")
        return False
    key = url[len(expected_prefix):]  
    if not key:
        logger.error("s3_delete: extracted key is empty — malformed URL")
        return False
    try:
        _s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        logger.info(f"Deleted from S3: {key}")
        return True
    except ClientError as e:
        logger.error(f"S3 delete failed: {e.response['Error']['Code']} — {e.response['Error']['Message']}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during S3 delete: {e}")
        return False