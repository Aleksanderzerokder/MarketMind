# Файл: agents/audience_agent.py (НОВАЯ ВЕРСИЯ ДЛЯ СРАВНЕНИЯ)
from typing import Dict, Any

class AudienceAgent:
    def __init__(self):
        print(" - AudienceAgent (процессор) инициализирован.")

    def analyze(self, analytics_data_by_period: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Анализирует данные по статистике для ДВУХ периодов.
        """
        print(f"   [AudienceAgent]: Сравнительный анализ статистики воронки...")
        
        results_by_period = {}

        # Проходим по каждому периоду ('period_1', 'period_2')
        for period_name, period_data in analytics_data_by_period.items():

            if not period_data:
                results_by_period[period_name] = {"error": f"Нет данных по статистике для {period_name}."}
                continue

            # Ваша логика извлечения данных, теперь внутри цикла
            open_card_count = period_data.get("openCardCount", 0)
            add_to_cart_count = period_data.get("addToCartCount", 0)
            orders_count = period_data.get("ordersCount", 0)
            
            print(f"     - {period_name}: Просмотров: {open_card_count}, В корзину: {add_to_cart_count}, Заказов: {orders_count}")

            # Сохраняем результат для этого периода
            results_by_period[period_name] = {
                "open_card_count": open_card_count,
                "add_to_cart_count": add_to_cart_count,
                "orders_count": orders_count,
                "orders_sum_rub": period_data.get("ordersSumRub", 0),
                "buyouts_count": period_data.get("buyoutsCount", 0),
                "buyouts_sum_rub": period_data.get("buyoutsSumRub", 0),
                "conversion_to_cart_percent": period_data.get("conversionToCart", 0),
                "buyout_percent": period_data.get("buyoutPercent", 0)
            }
        
        return results_by_period
