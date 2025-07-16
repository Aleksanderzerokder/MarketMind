# Файл: main.py (ФИНАЛЬНАЯ ВЕРСИЯ ДЛЯ СВОДНОГО ОТЧЕТА)
import sys
import os
import logging
import uuid
import redis

from fastapi import FastAPI, HTTPException
from schemas.models import AnalysisRequest, QuestionRequest
from decision_agent.manager import DecisionManager
from llm.generator import generate_hybrid_report, answer_question
from config import MARKETPLACE_API_KEY, GIGACHAT_CREDENTIALS
from utils import cache 
from utils.marketplace_api import get_all_wb_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Мультиагентная аналитическая система", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    logger.info("Сервер запускается, пытаюсь подключиться к Redis...")
    try:
        cache.redis_client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", 6379)),
            db=int(os.environ.get("REDIS_DB", 0)),
            decode_responses=True
        )
        cache.redis_client.ping()
        logger.info("Успешное подключение к Redis.")
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Не удалось подключиться к Redis: {e}")
        logger.warning("Кэширование будет отключено.")
        cache.redis_client = None

@app.on_event("shutdown")
async def shutdown_event():
    if cache.redis_client:
        logger.info("Закрываю соединение с Redis...")
        cache.redis_client.close()

@app.get("/products")
async def get_product_list():
    logger.info("Получен запрос на список всех товаров...")
    if not MARKETPLACE_API_KEY:
        raise HTTPException(status_code=500, detail="API ключ маркетплейса не настроен.")
    product_data = get_all_wb_products(api_key=MARKETPLACE_API_KEY)
    if "error" in product_data:
        raise HTTPException(status_code=502, detail=f"Ошибка API: {product_data['error']}")
    return product_data

@app.post("/analyze")
async def analyze_products(request: AnalysisRequest):
    """
    ИЗМЕНЕНО: Генерирует и объединяет СРАВНИТЕЛЬНЫЕ отчеты.
    """
    if not MARKETPLACE_API_KEY or not GIGACHAT_CREDENTIALS:
        raise HTTPException(status_code=500, detail="API ключи не настроены.")

    logger.info("Шаг 1: Запуск Управляющего Агента для сбора данных за 2 периода...")
    manager = DecisionManager(marketplace_api_key=MARKETPLACE_API_KEY)
    
    # Преобразуем Pydantic-модели в простые словари для передачи
    period_1_dict = {'date_from': request.period_1.date_from.isoformat(), 'date_to': request.period_1.date_to.isoformat()}
    period_2_dict = {'date_from': request.period_2.date_from.isoformat(), 'date_to': request.period_2.date_to.isoformat()}

    raw_results = manager.run_analysis(
        sku_list=request.sku_list,
        period_1=period_1_dict,
        period_2=period_2_dict,
        cost_prices=request.cost_prices
    )
    
    if "error" in raw_results:
        logger.error(f"Управляющий агент вернул ошибку: {raw_results['error']}")
        raise HTTPException(status_code=502, detail=raw_results['error'])
        
    logger.info("Сбор данных и анализ завершены.")

    logger.info("Шаг 2: Генерация сводного сравнительного отчета с помощью LLM...")
    
    all_reports = []
    for sku, analysis_data in raw_results.items():
        if "error" in analysis_data:
            all_reports.append(f"### Анализ для {sku} не удался: {analysis_data['error']}")
            continue

        single_sku_data = {sku: analysis_data}
        
        # ВЫЗЫВАЕМ НОВУЮ ФУНКЦИЮ
        comparison_report = generate_hybrid_report(
            single_sku_data, 
            period_1=period_1_dict,
            period_2=period_2_dict
        )
        all_reports.append(comparison_report)
    
    final_summary = "\n\n---\n\n".join(all_reports)
    logger.info("Сводный отчет успешно сгенерирован.")
    
    request_id = str(uuid.uuid4())
    if cache.redis_client:
        cache.cache_set(request_id, raw_results, ex=3600)
        logger.info(f"Результаты анализа для ID {request_id} сохранены в кэш.")

    return {
        "request_id": request_id,
        "llm_summary": final_summary,
        "raw_data": raw_results
    }

@app.post("/question")
async def ask_question(request: QuestionRequest):
    logger.info(f"Получен уточняющий вопрос по request_id: {request.request_id}")
    full_report = cache.cache_get(request.request_id)
    if not full_report:
        raise HTTPException(status_code=404, detail="Анализ с таким ID не найден.")
    
    sku_data = full_report.get(request.sku)
    if not sku_data:
        raise HTTPException(status_code=404, detail=f"Товар с SKU {request.sku} не найден.")
        
    aspect_data = sku_data.get(request.aspect)
    if not aspect_data:
        raise HTTPException(status_code=404, detail=f"Аспект '{request.aspect}' не найден.")
        
    llm_answer = answer_question(
        raw_data_for_aspect=aspect_data,
        aspect_name=request.aspect,
        sku=request.sku
    )
    return {"answer": llm_answer}