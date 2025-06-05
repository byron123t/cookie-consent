"""Redis connection management."""

from pathlib import Path

from redis import Redis

REDIS_URL = (Path(__file__).parent / 'redis_url.txt').read_text()


def get_connection():
    return Redis.from_url(REDIS_URL)
