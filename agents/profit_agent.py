# Файл: agents/profit_agent.py (НОВАЯ ВЕРСИЯ)
class ProfitAgent:
    def __init__(self):
        # Убираем cost_price из __init__
        print(" - ProfitAgent (вычислитель) инициализирован.")

    def analyze(self, sales_data: dict, cost_price: float) -> dict:
        """
        Вычисляет прибыльность, используя ПЕРЕДАННУЮ себестоимость.
        """
        print(f"   [ProfitAgent]: Расчет прибыльности с себестоимостью: {cost_price} руб.")
        
        items_sold = sales_data.get("units_ordered", 0)
        net_revenue = sales_data.get("net_revenue_rub", 0)
        
        # Используем переданную себестоимость
        total_cost = items_sold * cost_price
        profit = net_revenue - total_cost
        margin = (profit / net_revenue * 100) if net_revenue else 0
        
        return {
            "units_sold": items_sold,
            "net_revenue_rub": net_revenue,
            "total_cost_price_rub": round(total_cost, 2),
            "profit_rub": round(profit, 2),
            "profit_margin_percent": round(margin, 2),
            "cost_price_per_unit": cost_price, # Возвращаем фактическую себестоимость
            "data_source": "realization_report_net_revenue"
        }
