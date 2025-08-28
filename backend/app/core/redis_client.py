from redis import Redis
from .config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

def redis_ping() -> bool:
    try:
        return redis_client.ping()
    except Exception:
        return False