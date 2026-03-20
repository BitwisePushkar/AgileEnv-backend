import redis
import logging
from app.utils.settings import settings 

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        try:
            self.client = redis.Redis(host=settings.REDIS_HOST,
                                      port=settings.REDIS_PORT,
                                      db=0,
                                      decode_responses=True,
                                      socket_connect_timeout=5,
                                      socket_timeout=5,
                                      max_connections=50,
                                      retry_on_timeout=True,)
            self.client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def set_with_expiry(self, key: str, value: str, expiry_seconds: int) -> bool:
        try:
            self.client.setex(key, expiry_seconds, value)
            return True
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on SET: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Redis SET error: {str(e)}")
            return False

    def get(self, key: str):
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {str(e)}")
            return False

    def blacklist_token(self, token: str, ttl_seconds: int) -> bool:
        key = f"blacklist:{token}"
        return self.set_with_expiry(key, "1", ttl_seconds)

    def is_token_blacklisted(self, token: str) -> bool:
        return self.exists(f"blacklist:{token}")

redis_client = RedisClient()