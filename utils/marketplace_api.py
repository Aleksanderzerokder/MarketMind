# Файл: utils/marketplace_api.py (добавляем финальный отчет)
import requests
import datetime
import json
import time
from typing import Dict, Any, List

# ... (URL-ы остаются без изменений) ...
WB_CONTENT_API_URL = "https://content-api.wildberries.ru"
WB_API_V1_URL = "https://statistics-api.wildberries.ru/api/v1"
WB_API_V5_URL = "https://statistics-api.wildberries.ru/api/v5"
WB_ADS_API_URL = "https://advert-api.wildberries.ru"
WB_FEEDBACKS_API_URL = "https://feedbacks-api.wildberries.ru/api/v1"


def get_wb_realization_report(api_key: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
    """
    ФИНАЛЬНАЯ ВЕРСИЯ: Получает отчет о реализации с УМНОЙ пагинацией.
    """
    url = WB_API_V5_URL + "/supplier/reportDetailByPeriod"
    headers = {'Authorization': f'Bearer {api_key}'}
            
    limit = 100000 # Максимальный лимит на одну порцию
    params = {
        "dateFrom": date_from, # Используем переданную дату
        "dateTo": date_to,     # Используем переданную дату
        "limit": limit, "rrdid": 0
    }
    
    print(f"-> API (v5, Реализация): Запрос финального отчета о продажах с {params['dateFrom']}...")
    all_records = []
    
    while True:
        try:
            print(f"   - Запрос порции данных, начиная с rrdid: {params['rrdid']}...")
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            
            records = response.json()
            
            if records is None:
                print("   - Получен 'null' ответ, все данные загружены.")
                break
            
            if isinstance(records, dict) and "errors" in records and records["errors"]:
                 print(f"   [WARN] API Wildberries вернуло ошибку: {records['errors']}")
                 break

            if not records:
                print("   - Получен пустой список, все данные загружены.")
                break
                
            all_records.extend(records)
            print(f"   - Успешно получено {len(records)} записей. Всего загружено: {len(all_records)}.")
            
            # --- УМНЫЙ ВЫХОД ИЗ ЦИКЛА ---
            # 1. Если записей меньше лимита, это точно последняя страница.
            # 2. Проверяем наличие 'rrdid' в последней записи.
            if len(records) < limit or 'rrdid' not in records[-1]:
                print("   - Обнаружена последняя страница данных.")
                break
            
            params['rrdid'] = records[-1]['rrdid']
            time.sleep(1.2)

        except requests.RequestException as e:
            print(f"[ERROR] Критическая ошибка при запросе отчета: {e}")
            break
        except (KeyError, IndexError) as e:
             print(f"   - Завершение: не удалось получить rrdid для пагинации. Ошибка: {e}")
             break
             
    print(f"-> API (v5, Реализация): Финальный отчет, содержащий {len(all_records)} записей, успешно собран.")
    return all_records


def get_all_wb_products(api_key: str) -> Dict[str, Any]:
    url = WB_API_V1_URL + "/supplier/stocks"
    headers = {'Authorization': f'Bearer {api_key}'}
    print(f"-> API (v1): Запрос базового списка товаров (остатки)...")
    try:
        params = {'dateFrom': datetime.datetime(2020, 1, 1).isoformat()}
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return {"products": []}
        print(f"-> API (v1): Базовый список из {len(data)} товаров получен.")
        return {"products": data}
    except requests.RequestException as e:
        error_message = f"Ошибка API при получении списка товаров: {e}"
        if e.response is not None:
            error_message += f" | Ответ сервера: {e.response.text}"
        return {"error": error_message}

def get_wb_product_cards_details(api_key: str, nm_ids: List[int]) -> List[Dict[str, Any]]:
    """
    ФИНАЛЬНАЯ ВЕРСИЯ: Получает детальную информацию по списку nmID.
    """
    url = WB_CONTENT_API_URL + "/content/v2/get/cards/list"
    headers = {'Authorization': f'Bearer {api_key}'}
    all_cards = []
    chunk_size = 100
    
    print(f"-> API (Content v2): Запрос полной информации для {len(nm_ids)} карточек по nmID...")
    
    for i in range(0, len(nm_ids), chunk_size):
        chunk = nm_ids[i:i + chunk_size]
        payload = {
            "settings": {
                # ИЗМЕНЕНО: Фильтруем по nmID, а не по vendorCodes
                "filter": {"nmIDs": chunk},
                "allowedCategoriesOnly": False # Получаем все категории
            }
        }
        print(f"   - Отправка порции {i//chunk_size + 1} (nmID с {i} по {i + len(chunk) - 1})...")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            if "error" in data and data["error"]:
                error_text = data.get("errorText", "Неизвестная ошибка API контента")
                print(f"   [WARN] Ошибка от API контента в порции: {error_text}.")
                continue
                
            chunk_cards = data.get("cards", [])
            all_cards.extend(chunk_cards)
            print(f"   - Успешно получено {len(chunk_cards)} карточек.")
            time.sleep(1)
        except requests.RequestException as e:
            print(f"   [ERROR] Критическая ошибка при запросе порции: {e}.")
            continue
            
    print(f"-> API (Content v2): Итоговая информация по {len(all_cards)} карточкам успешно собрана.")
    return all_cards

def get_wb_orders_report(api_key: str, period_days: int) -> Dict[str, Any]:
    url = WB_API_V1_URL + "/supplier/orders"
    date_from = (datetime.datetime.now() - datetime.timedelta(days=period_days)).strftime('%Y-%m-%dT00:00:00')
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'dateFrom': date_from, 'flag': 1}
    print(f"-> API: Запрос отчета о ЗАКАЗАХ с {date_from}...")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return {"data": response.json()}
    except requests.RequestException as e:
        return {"data": {"error": f"Ошибка при получении заказов: {e}"}}

def get_wb_analytics_by_sku(api_key: str, nm_ids: list[int], date_from: str, date_to: str) -> dict:
    url = WB_API_V5_URL + "/supplier/reportDetailByPeriod"
    headers = {'Authorization': f'Bearer {api_key}'}
    
    payload = {
        "nmIDs": nm_ids,
        "period": { "begin": date_from, "end": date_to }, # Используем переданные даты
        "page": 1
    }
    print(f"-> API (v5): Запрос аналитики для {len(nm_ids)} SKU...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
             return {"error": data.get("errorText", "Неизвестная ошибка от WB API v5")}
        return data.get("data", {}).get("cards", [])
    except requests.RequestException as e:
        return {"error": f"Ошибка API v5 при получении аналитики: {e}"}

def get_wb_ads_list(api_key: str) -> List[Dict[str, Any]]:
    url = WB_ADS_API_URL + "/adv/v1/promotion/adverts"
    headers = {'Authorization': f'Bearer {api_key}'}
    print("-> API: Запрос списка рекламных кампаний...")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

def get_wb_reviews(api_key: str, nm_id: int) -> List[Dict[str, Any]]:
    """
    ФИНАЛЬНАЯ ВЕРСИЯ V6: Возвращаемся к v1 API, но запрашиваем и активные, и архивные отзывы.
    """
    all_reviews = []
    headers = {'Authorization': f'Bearer {api_key}'}
    
    # --- Шаг 1: Запрашиваем АКТИВНЫЕ отзывы ---
    try:
        url_active = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks"
        # Убираем isAnswered, чтобы получить ВСЕ активные
        params_active = {'nmId': nm_id, 'take': 5000, 'skip': 0, 'order': 'dateDesc'}
        print(f"-> API (v1, Активные): Запрос активных отзывов для nmId {nm_id}...")
        
        response_active = requests.get(url_active, headers=headers, params=params_active, timeout=30)
        response_active.raise_for_status()
        active_data = response_active.json()
        
        if active_data.get("error"):
            print(f"   [WARN] API v1 (активные) вернуло ошибку: {active_data.get('errorText')}")
        else:
            active_reviews = active_data.get("data", {}).get("feedbacks", [])
            all_reviews.extend(active_reviews)
            print(f"   - Найдено {len(active_reviews)} активных отзывов.")
            
    except requests.RequestException as e:
        print(f"   [ERROR] Ошибка при запросе активных отзывов v1: {e}")

    # --- Шаг 2: Запрашиваем АРХИВНЫЕ отзывы ---
    time.sleep(1.2) # Пауза между запросами
    try:
        url_archive = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks/archive"
        params_archive = {'nmId': nm_id, 'take': 5000, 'skip': 0}
        print(f"-> API (v1, Архив): Запрос архивных отзывов для nmId {nm_id}...")
        
        response_archive = requests.get(url_archive, headers=headers, params=params_archive, timeout=30)
        response_archive.raise_for_status()
        archive_data = response_archive.json()
        
        if archive_data.get("error"):
             print(f"   [WARN] API v1 (архив) вернуло ошибку: {archive_data.get('errorText')}")
        else:
            archive_reviews = archive_data.get("data", {}).get("feedbacks", [])
            all_reviews.extend(archive_reviews)
            print(f"   - Найдено {len(archive_reviews)} архивных отзывов.")

    except requests.RequestException as e:
        print(f"   [ERROR] Ошибка при запросе архивных отзывов v1: {e}")

    print(f"-> API (v1): Итоговый сбор для nmId {nm_id} завершен. Суммарно найдено {len(all_reviews)} отзывов.")
    return all_reviews