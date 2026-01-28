import os

import redis

DEFAULT_REDIS_URL = "redis://redis:6379/0"


def get_redis_connection():
    redis_url = os.environ.get("REDIS_URL", DEFAULT_REDIS_URL)
    return redis.from_url(redis_url)
