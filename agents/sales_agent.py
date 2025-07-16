# Файл: agents/sales_agent.py (ФИНАЛЬНАЯ ВЕРСИЯ ДЛЯ СРАВНЕНИЯ)
from typing import Dict, Any, List

class SalesAgent:
    def __init__(self):
        print(" - SalesAgent (процессор) инициализирован.")

    def analyze(self, sku: str, sales_reports: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Анализирует отчеты о реализации для ДВУХ периодов, сохраняя data_source.
        """
        print(f"   [SalesAgent]: Сравнительный анализ продаж для SKU '{sku}'...")
        
        results_by_period = {}
        normalized_sku = sku.replace(" ", "").lower()

        for period_name, report_data in sales_reports.items():
            
            if not report_data or (isinstance(report_data, dict) and "error" in report_data):
                results_by_period[period_name] = {"error": f"Отчет о реализации для {period_name} пуст."}
                continue

            total_gross_revenue = 0
            total_net_revenue = 0
            items_sold = 0
            
            for item in report_data:
                report_sku = item.get('sa_name')
                if not report_sku:
                    continue
                
                if normalized_sku == report_sku.replace(" ", "").lower():
                    if item.get("doc_type_name") == "Продажа":
                        quantity = item.get('quantity', 0)
                        if quantity == 0: continue
                        
                        total_gross_revenue += item.get('retail_price_withdisc_rub', 0)
                        total_net_revenue += item.get('ppvz_for_pay', 0)
                        items_sold += quantity

            print(f"     - {period_name}: Найдено {items_sold} проданных товаров. Gross: {total_gross_revenue:.2f}, Net: {total_net_revenue:.2f}")

            # --- ИСПРАВЛЕННЫЙ БЛОК: Сохраняем `data_source` ---
            results_by_period[period_name] = {
                "gross_revenue_rub": round(total_gross_revenue, 2),
                "net_revenue_rub": round(total_net_revenue, 2),
                "units_ordered": items_sold,
                "data_source": "wb_realization_report_api_v5" # Ваше поле на месте!
            }

        return results_by_period