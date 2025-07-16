# Файл: decision_agent/manager.py (ФИНАЛЬНАЯ ВЕРСИЯ С ТОЧНЫМИ ДАННЫМИ)
from typing import List, Dict, Any
from utils.marketplace_api import (
    get_all_wb_products,
    get_wb_product_cards_details,
    get_wb_realization_report, # ИМПОРТИРУЕМ НОВУЮ ФУНКЦИЮ
    get_wb_ads_list,
    get_wb_reviews,
    get_wb_analytics_by_sku
)

from agents.sales_agent import SalesAgent
from agents.card_agent import CardAgent
from agents.reviews_agent import ReviewsAgent
from agents.audience_agent import AudienceAgent
from agents.ads_agent import AdsAgent
from agents.profit_agent import ProfitAgent

class DecisionManager:
    def __init__(self, marketplace_api_key: str):
        self.api_key = marketplace_api_key
        print("-> DM: Инициализация всех агентов...")
        self.sales_agent = SalesAgent()
        self.card_agent = CardAgent()
        self.ads_agent = AdsAgent()
        self.reviews_agent = ReviewsAgent(api_key=self.api_key)
        self.audience_agent = AudienceAgent()
        self.profit_agent = ProfitAgent()
        print("Управляющий агент создан и готов к работе.")

    def run_analysis(self, sku_list: List[str] | str, period_1: Dict, period_2: Dict, cost_prices: Dict[str, float] = None) -> Dict[str, Any]:
        # Получаем даты из словарей
        p1_from, p1_to = period_1['date_from'], period_1['date_to']
        p2_from, p2_to = period_2['date_from'], period_2['date_to']

        if cost_prices is None:
            cost_prices = {}
          # --- Шаг 1: Получение и ПРАВИЛЬНАЯ АГРЕГАЦИЯ данных со всех складов ---
        print("-> DM: Шаг 1/3. Получаю и агрегирую данные по остаткам со всех складов...")
        base_products_data = get_all_wb_products(self.api_key)
        if "error" in base_products_data:
            return base_products_data

        product_map = {}
        # Проходим по каждой записи из API
        for item in base_products_data.get("products", []):
            sku = item.get("supplierArticle")
            if not sku: continue

            # Если SKU встречается впервые, создаем для него запись
            if sku not in product_map:
                product_map[sku] = item.copy()  # Копируем всю базовую информацию
                # Обнуляем остатки, чтобы начать суммировать с чистого листа
                product_map[sku]["quantity"] = 0
                product_map[sku]["quantityFull"] = 0
            
            # Суммируем остатки с каждого склада к уже существующим
            product_map[sku]["quantity"] += item.get("quantity", 0)
            product_map[sku]["quantityFull"] += item.get("quantityFull", 0)
        
        # --- Определяем, какие SKU анализировать ---
        if sku_list == "all":
            analysis_skus = list(product_map.keys())
        else:
            analysis_skus = [sku for sku in sku_list if sku in product_map]

        if not analysis_skus:
            return {"error": f"Ни один из запрошенных SKU не найден в вашем каталоге: {sku_list}"}
        
        # --- Шаг 2: Получение и слияние детальной информации ---
        # Собираем nmID ТОЛЬКО для тех SKU, которые мы будем анализировать.
        nm_ids_to_fetch_details = [product_map[sku].get("nmId") for sku in analysis_skus if product_map[sku].get("nmId")]
        
        print(f"-> DM: Шаг 2/3. Получаю детальную информацию для {len(nm_ids_to_fetch_details)} карточек по nmID...")
        detailed_cards_list = get_wb_product_cards_details(self.api_key, nm_ids_to_fetch_details)

        # Создаем временную карту {nmID -> детальная карточка} для быстрого поиска
        detailed_cards_map = {card['nmID']: card for card in detailed_cards_list}

        # НАДЕЖНОЕ ОБОГАЩЕНИЕ ДАННЫХ
        for sku in analysis_skus:
            base_info = product_map.get(sku)
            if not base_info: continue

            nm_id = base_info.get("nmId")
            # Если для этого nm_id нашлась детальная карточка, обогащаем базовую инфу
            if nm_id in detailed_cards_map:
                card_details = detailed_cards_map[nm_id]
                price_info_list = card_details.get("sizes", [{}])[0].get("priceInfos", [])
                price_info = price_info_list[0] if price_info_list else {}
                
                base_info.update({
                    "name": card_details.get("title"),
                    "brand": card_details.get("brand"),
                    "description": card_details.get("description", ""),
                    "characteristics": card_details.get("characteristics", []),
                    "photos_count": len(card_details.get("photos", [])) if card_details.get("photos") else 0,
                    "videos_count": len(card_details.get("videos", [])) if card_details.get("videos") else 0,
                    "subjectID": card_details.get("subjectID") or card_details.get("subjectId"),
                    "priceU": price_info.get("price", 0) * 100,
                    "salePriceU": price_info.get("discountedPrice", 0) * 100,
                    "Price": price_info.get("price", 0),
                    "Discount": price_info.get("discount", 0),
                })
            else:
                 base_info['warning'] = f"Для nmId {nm_id} не найдена детальная карточка в Content API."


        # --- Шаг 3: Предварительная загрузка отчетов для анализа ---
        print("-> DM: Шаг 3/4. Предварительная загрузка отчетов для ДВУХ периодов...")
        
        # Данные, не зависящие от периода, запрашиваем один раз
        ads_report = get_wb_ads_list(self.api_key)
        all_nm_ids = [card.get("nmId") for card in product_map.values() if card.get("nmId")]

        print(f"   - Загружаю отчеты для Периода 1 ({p1_from} - {p1_to})")
        sales_report_p1 = get_wb_realization_report(self.api_key, p1_from, p1_to)
        analytics_data_list_p1 = get_wb_analytics_by_sku(self.api_key, all_nm_ids, p1_from, p1_to)
        # ИСПРАВЛЕНИЕ: Проверяем, что analytics_data_list_p1 это список, а не словарь с ошибкой
        analytics_map_p1 = {item['nmID']: item for item in analytics_data_list_p1} if isinstance(analytics_data_list_p1, list) else {}

        print(f"   - Загружаю отчеты для Периода 2 ({p2_from} - {p2_to})")
        sales_report_p2 = get_wb_realization_report(self.api_key, p2_from, p2_to)
        analytics_data_list_p2 = get_wb_analytics_by_sku(self.api_key, all_nm_ids, p2_from, p2_to)
        # ИСПРАВЛЕНИЕ: Такая же проверка для второго периода
        analytics_map_p2 = {item['nmID']: item for item in analytics_data_list_p2} if isinstance(analytics_data_list_p2, list) else {}

        print("-> DM: Предзагрузка завершена.")

        # --- Финальный цикл анализа ---
        full_analysis_report = {}
        print(f"\n--- Начинаю итоговый анализ для {len(analysis_skus)} SKU... ---")
        
        for sku in analysis_skus:
            product_card = product_map.get(sku)
            if not product_card: continue

            # Ваш диагностический жучок
            print("\n" + "="*20 + f" [DEBUG] Данные для CardAgent (SKU: {sku}) " + "="*20)
            import json
            print(json.dumps(product_card, indent=2, ensure_ascii=False))
            print("="*80 + "\n")

            print(f"Анализ товара SKU: {sku}")
            sku_report = {}
            if not product_card.get("nmId"):
                full_analysis_report[sku] = {"error": "Не удалось получить nmId для этого товара."}
                continue
            
            nm_id = product_card.get("nmId")
            
            # Вызываем всех агентов
            sku_report['card'] = self.card_agent.analyze(product_card=product_card)
            sku_report['sales'] = self.sales_agent.analyze(
                sku=sku, 
                sales_reports={'period_1': sales_report_p1, 'period_2': sales_report_p2}
            )
            sku_report['ads'] = self.ads_agent.analyze(nm_id=nm_id, full_ads_report=ads_report)
            sku_report['audience'] = self.audience_agent.analyze(
                analytics_data_by_period={'period_1': analytics_map_p1.get(nm_id, {}), 'period_2': analytics_map_p2.get(nm_id, {})}
            )
            sku_report['reviews'] = self.reviews_agent.analyze(nm_id=nm_id)
            
            # --- ЕДИНСТВЕННЫЙ, ПРАВИЛЬНЫЙ ВЫЗОВ PROFIT AGENT ---
            current_cost_price = cost_prices.get(sku, 150.0)
            sku_report['profit'] = self.profit_agent.analyze(
                sales_data=sku_report.get('sales', {}).get('period_1', {}), # ВАЖНО: берем данные за period_1,
                cost_price=current_cost_price
            )
            
            # Правильный отступ
            full_analysis_report[sku] = sku_report

        print("\n--- Полный анализ завершен. ---")
        return full_analysis_report