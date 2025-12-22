import boto3
from botocore.exceptions import ClientError
from functools import lru_cache
from app import config
import uuid
import logging

logger = logging.getLogger(__name__)

@lru_cache
def get_settings():
    return config.Settings()

settings=get_settings()

AWS_ACCESS_KEY_ID=settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=settings.AWS_SECRET_ACCESS_KEY
AWS_REGION=settings.AWS_REGION
S3_BUCKET_NAME=settings.S3_BUCKET_NAME

s3_client=boto3.client('s3',aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY,region_name=AWS_REGION)

def s3_upload(content:bytes,name:str,type:str):
    try:
        ext=name.split('.')[-1] if '.' in name else ''
        unique_name=f"profile_images/{uuid.uuid4()}.{ext}"
        s3_client.put_object(Bucket=S3_BUCKET_NAME,Key=unique_name,Body=content,ContentType=type)
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_name}"
        logger.info(f"File uploaded successfully to S3: {s3_url}")
        return s3_url
    except ClientError as e:
        logger.error(f"Error uploading file to S3: {e}")
        return None

def s3_delete(url:str)->bool:
    try:
        key=url.split(f"{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/")[1]
        s3_client.delete_object(Bucket=S3_BUCKET_NAME,Key=key)
        logger.info(f"File deleted successfully from S3: {key}")
        return True 
    except Exception as e:
        logger.error(f"Error deleting file from S3: {e}")
        return False

def validate_image(name:str,size:int,max_size:int=5):
    allowed={'png','jpg','jpeg','gif','webp'}
    file_ext=name.lower().split('.')[-1]
    if file_ext not in allowed:
        return False
    if size>0:
        max_size_bytes=max_size * 1024 * 1024
        if size>max_size_bytes:
            return False
    return True