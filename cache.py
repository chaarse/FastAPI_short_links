import redis
from fastapi import HTTPException

# Подключение к Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def get_cached_url(short_code: str) -> str | None:
    """
    Получает оригинальный URL из кэша Redis.
    """
    return redis_client.get(f"url:{short_code}")

def set_cached_url(short_code: str, original_url: str, expire: int = 3600):
    """
    Сохраняет оригинальный URL в кэше Redis.
    expire: время жизни кэша в секундах (по умолчанию 1 час).
    """
    redis_client.set(f"url:{short_code}", original_url, ex=expire)

def delete_cached_url(short_code: str):
    """
    Удаляет кэшированный URL из Redis.
    """
    redis_client.delete(f"url:{short_code}")

def get_cached_stats(short_code: str) -> dict | None:
    """
    Получает статистику по ссылке из кэша Redis.
    """
    return redis_client.hgetall(f"stats:{short_code}")

def set_cached_stats(short_code: str, stats: dict, expire: int = 3600):
    """
    Сохраняет статистику по ссылке в кэше Redis.
    expire: время жизни кэша в секундах (по умолчанию 1 час).
    """
    redis_client.hset(f"stats:{short_code}", mapping=stats)
    redis_client.expire(f"stats:{short_code}", expire)

def delete_cached_stats(short_code: str):
    """
    Удаляет кэшированную статистику из Redis.
    """
    redis_client.delete(f"stats:{short_code}")