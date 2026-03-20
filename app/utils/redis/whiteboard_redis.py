import json
import logging
from typing import List, Optional
import redis
from app.utils.settings import settings

logger = logging.getLogger(__name__)

PRESENCE_TTL = 120  
CURSOR_TTL = 30    
DELTA_TTL = 300  

_redis: Optional[redis.Redis] = None

def get_wb_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.Redis(host=settings.REDIS_HOST, 
                             port=settings.REDIS_PORT,
                             db=1,
                             decode_responses=True,
                             socket_connect_timeout=5,
                             socket_timeout=5,
                             max_connections=50,
                             retry_on_timeout=True,)
    return _redis

def set_user_present(whiteboard_id: int, user_id: int, user_info: dict) -> None:
    r = get_wb_redis()
    key = f"wb:presence:{whiteboard_id}"
    try:
        r.hset(key, str(user_id), json.dumps(user_info))
        r.expire(key, PRESENCE_TTL)
    except Exception as exc:
        logger.error("Redis presence set error board=%s user=%s: %s", whiteboard_id, user_id, exc)

def remove_user_presence(whiteboard_id: int, user_id: int) -> None:
    r = get_wb_redis()
    try:
        r.hdel(f"wb:presence:{whiteboard_id}", str(user_id))
    except Exception as exc:
        logger.error("Redis presence remove error board=%s user=%s: %s", whiteboard_id, user_id, exc)

def get_online_users(whiteboard_id: int) -> List[dict]:
    r = get_wb_redis()
    try:
        raw = r.hgetall(f"wb:presence:{whiteboard_id}")
        return [json.loads(v) for v in raw.values()]
    except Exception as exc:
        logger.error("Redis presence get error board=%s: %s", whiteboard_id, exc)
        return []

def update_cursor(whiteboard_id: int, user_id: int, x: float, y: float) -> None:
    r = get_wb_redis()
    try:
        r.setex(f"wb:cursor:{whiteboard_id}:{user_id}",CURSOR_TTL,json.dumps({"x": x, "y": y, "user_id": user_id}),)
    except Exception as exc:
        logger.error("Redis cursor update error board=%s user=%s: %s", whiteboard_id, user_id, exc)

def get_all_cursors(whiteboard_id: int) -> List[dict]:
    r = get_wb_redis()
    try:
        keys = r.keys(f"wb:cursor:{whiteboard_id}:*")
        if not keys:
            return []
        pipe = r.pipeline()
        for k in keys:
            pipe.get(k)
        values = pipe.execute()
        result = []
        for v in values:
            if v:
                try:
                    result.append(json.loads(v))
                except json.JSONDecodeError:
                    pass
        return result
    except Exception as exc:
        logger.error("Redis get_all_cursors error board=%s: %s", whiteboard_id, exc)
        return []

def remove_cursor(whiteboard_id: int, user_id: int) -> None:
    r = get_wb_redis()
    try:
        r.delete(f"wb:cursor:{whiteboard_id}:{user_id}")
    except Exception as exc:
        logger.error("Redis cursor remove error board=%s user=%s: %s", whiteboard_id, user_id, exc)

def append_draw_delta(whiteboard_id: int, temp_id: str, points: list) -> None:
    r = get_wb_redis()
    key = f"wb:delta:{whiteboard_id}:{temp_id}"
    try:
        r.rpush(key, json.dumps(points))
        r.expire(key, DELTA_TTL)
    except Exception as exc:
        logger.error("Redis draw delta append error board=%s temp=%s: %s", whiteboard_id, temp_id, exc)

def get_draw_deltas(whiteboard_id: int, temp_id: str) -> List[list]:
    r = get_wb_redis()
    try:
        raw = r.lrange(f"wb:delta:{whiteboard_id}:{temp_id}", 0, -1)
        return [json.loads(chunk) for chunk in raw]
    except Exception as exc:
        logger.error("Redis draw delta get error board=%s temp=%s: %s", whiteboard_id, temp_id, exc)
        return []

def clear_draw_deltas(whiteboard_id: int, temp_id: str) -> None:
    r = get_wb_redis()
    try:
        r.delete(f"wb:delta:{whiteboard_id}:{temp_id}")
    except Exception as exc:
        logger.error("Redis draw delta clear error board=%s temp=%s: %s", whiteboard_id, temp_id, exc)

def publish_event(whiteboard_id: int, event: dict) -> None:
    r = get_wb_redis()
    try:
        r.publish(f"wb:channel:{whiteboard_id}", json.dumps(event))
    except Exception as exc:
        logger.error("Redis publish error board=%s: %s", whiteboard_id, exc)

def get_pubsub(whiteboard_id: int) -> redis.client.PubSub:
    r = get_wb_redis()
    ps = r.pubsub(ignore_subscribe_messages=True)
    ps.subscribe(f"wb:channel:{whiteboard_id}")
    return ps