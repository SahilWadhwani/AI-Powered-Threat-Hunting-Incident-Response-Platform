from typing import Optional
from functools import lru_cache
from ..core.redis_client import redis_client
from ..core.config import settings

# GeoIP reader is optional
try:
    import geoip2.database  # type: ignore
except Exception:
    geoip2 = None  # type: ignore

CACHE_PREFIX = "geoip:country:"

@lru_cache(maxsize=1)
def _get_reader():
    # Lazy init; returns None if no DB path or geoip2 missing
    if geoip2 is None:
        return None
    path = settings.geoip_db_path
    if not path:
        return None
    try:
        return geoip2.database.Reader(path)
    except Exception:
        return None

def country_for_ip(ip: str | None) -> Optional[str]:
    if not ip:
        return None

    # Redis cache first
    key = f"{CACHE_PREFIX}{ip}"
    try:
        cached = redis_client.get(key)
        if cached:
            return cached
    except Exception:
        pass  # cache is optional

    reader = _get_reader()
    if reader is None:
        return None

    try:
        rec = reader.country(ip)
        code = rec.country.iso_code  # e.g., "US"
    except Exception:
        code = None

    try:
        if code:
            # cache for 1 day
            redis_client.setex(key, 86400, code)
    except Exception:
        pass

    return code