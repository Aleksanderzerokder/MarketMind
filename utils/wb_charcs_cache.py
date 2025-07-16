# utils/wb_charcs_cache.py
import requests
from config import MARKETPLACE_API_KEY

_charcs_cache = {}

def get_required_charcs(subject_id: int) -> set:
    if subject_id in _charcs_cache:
        return _charcs_cache[subject_id]
    url = f"https://suppliers-api.wildberries.ru/public/api/v1/object/charcs/{subject_id}"
    headers = {"Authorization": f"Bearer {MARKETPLACE_API_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        required = {char['name'] for char in data if char.get('required')}
        _charcs_cache[subject_id] = required
        return required
    except Exception as e:
        print(f"[Charcs]: Ошибка при запросе: {e}")
        return set()
