import redis
from functools import lru_cache
from app import config
import logging

logger = logging.getLogger(__name__)

@lru_cache
def get_settings():
    return config.Settings()

settings = get_settings()

class RedisClient:
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.client.ping()
            logger.info(f"Successfully connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def set_with_expiry(self, key: str, value: str, expiry_seconds: int) -> bool:
        """Set a key with expiration time"""
        try:
            self.client.setex(key, expiry_seconds, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {str(e)}")
            return False
    
    def get(self, key: str) -> str:
        """Get value by key"""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {str(e)}")
            return False

redis_client = RedisClient()