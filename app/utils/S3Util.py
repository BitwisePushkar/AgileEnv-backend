import logging
import uuid
from enum import Enum
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from app.utils.settings import settings

logger = logging.getLogger(__name__)

class UploadFolder(str, Enum):
    PROFILE = "profile_images"
    CHAT = "chat_files"

_SIZE_LIMITS: dict[str, int] = {
    "image": 5  * 1024 * 1024,  
    "audio": 20 * 1024 * 1024,  
    "file":  50 * 1024 * 1024, 
    "video": 100 * 1024 * 1024,
}

_ALLOWED_PROFILE_EXTENSIONS: frozenset[str] = frozenset({"png", "jpg", "jpeg", "gif", "webp"})
_ALLOWED_CHAT_EXTENSIONS: frozenset[str] = frozenset({"png", "jpg", "jpeg", "gif", "webp","mp3", "ogg",
                                                      "wav", "m4a", "aac","pdf", "doc", "docx", "xls",
                                                      "xlsx", "ppt", "pptx", "txt", "csv","mp4", "mov", 
                                                      "avi", "mkv", "webm", })
_EXT_TO_MESSAGE_TYPE: dict[str, str] = {
    "png": "image", "jpg": "image", "jpeg": "image", "gif": "image", "webp": "image",
    "mp3": "audio", "ogg": "audio", "wav": "audio", "m4a": "audio", "aac": "audio",
    "pdf": "file",  "doc": "file",  "docx": "file",  "xls": "file",  "xlsx": "file",
    "ppt": "file",  "pptx": "file", "txt": "file",   "csv": "file",
    "mp4": "video", "mov": "video", "avi": "video", "mkv": "video", "webm": "video",
}
_s3_client = None

def _get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3",aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,region_name = settings.AWS_REGION,)
    return _s3_client

def _extract_ext(filename: str) -> Optional[str]:
    if "." not in filename:
        return None
    return filename.lower().rsplit(".", 1)[-1]

def validate_image(filename: str, size: Optional[int] = None) -> tuple[bool, str]:
    ext = _extract_ext(filename)
    if not ext:
        return False, "File has no extension"
    if ext not in _ALLOWED_PROFILE_EXTENSIONS:
        return False, f"Extension '{ext}' is not allowed for profile images"
    limit = _SIZE_LIMITS["image"]
    if size is not None and size > limit:
        return False, f"File too large: {size} bytes (max {limit // (1024*1024)} MB)"
    return True, ""

def validate_chat_file(filename: str, size: Optional[int] = None) -> tuple[bool, str, str]:
    ext = _extract_ext(filename)
    if not ext:
        return False, "File has no extension", ""
    if ext not in _ALLOWED_CHAT_EXTENSIONS:
        return False, f"Extension '{ext}' is not allowed in chat", ""
    msg_type = _EXT_TO_MESSAGE_TYPE.get(ext, "file")
    limit = _SIZE_LIMITS.get(msg_type, _SIZE_LIMITS["file"])
    if size is not None and size > limit:
        mb = limit // (1024 * 1024)
        return False, f"File too large: {size} bytes (max {mb} MB for {msg_type})", ""
    return True, "", msg_type

def s3_upload(content: bytes,filename: str,content_type: str,folder: UploadFolder = UploadFolder.PROFILE,) -> Optional[str]:
    ext = _extract_ext(filename) or "bin"
    key = f"{folder.value}/{uuid.uuid4()}.{ext}"
    try:
        _get_client().put_object(Bucket = settings.S3_BUCKET_NAME,Key = key,Body = content,ContentType = content_type,)
        url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        logger.info("S3 upload OK: %s", url)
        return url
    except ClientError as exc:
        err = exc.response["Error"]
        logger.error("S3 upload failed [%s]: %s", err["Code"], err["Message"])
        return None
    except Exception as exc:
        logger.error("S3 upload unexpected error: %s", exc)
        return None
    except Exception as exc:
        logger.error("S3 upload unexpected error: %s", exc)
        return None

def s3_delete(key: str) -> bool:
    legacy_prefix = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/"
    if key.startswith("https://"):
        if not key.startswith(legacy_prefix):
            logger.error("s3_delete: URL doesn't match expected bucket. Got: %s", key[:80])
            return False
        key = key[len(legacy_prefix):]
    if not key:
        logger.error("s3_delete: empty key")
        return False
    try:
        _get_client().delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        logger.info("S3 delete OK: %s", key)
        return True
    except ClientError as exc:
        err = exc.response["Error"]
        logger.error("S3 delete failed [%s]: %s", err["Code"], err["Message"])
        return False
    except Exception as exc:
        logger.error("S3 delete unexpected error: %s", exc)
        return False

def upload_chat_file(content: bytes,filename: str,content_type: str,) -> tuple[Optional[str], str]:
    valid, reason, msg_type = validate_chat_file(filename, size=len(content))
    if not valid:
        logger.warning("Chat file rejected: %s — %s", filename, reason)
        return None, ""
    
    url = s3_upload(content, filename, content_type, folder=UploadFolder.CHAT)
    return url, msg_type
