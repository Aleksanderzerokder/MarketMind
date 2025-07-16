# Файл: utils/cache.py
import os
import redis
import json

# --- ИЗМЕНЕНИЕ: Мы больше не создаем клиент здесь! ---
# Мы просто объявляем переменную, которую main.py заполнит позже.
redis_client: redis.Redis = None

# Функции остаются прежними, они будут использовать клиент,
# когда он будет создан.
def cache_set(key, value, ex=None):
    if not redis_client:
        print("[WARN] Redis client не инициализирован. Кэширование пропускается.")
        return
    redis_client.set(key, json.dumps(value), ex=ex)

def cache_get(key):
    if not redis_client:
        print("[WARN] Redis client не инициализирован. Кэширование пропускается.")
        return None
    val = redis_client.get(key)
    if val is None:
        return None
    # decode_responses=True в клиенте уже делает .decode('utf-8')
    return json.loads(val)