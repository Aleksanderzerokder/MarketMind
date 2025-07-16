# Файл: agents/price_agent.py
from utils.marketplace_api import get_wb_price

class PriceAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        print(" - PriceAgent (сборщик) инициализирован.")

    def analyze(self, nm_id: int) -> dict:
        """Получает цену для конкретного nm_id."""
        print(f"   [PriceAgent]: Запрос цены для nmId {nm_id}...")
        if not nm_id:
            return {"error": "nmId not provided"}
        price = get_wb_price(self.api_key, nm_id)
        if isinstance(price, dict) and "error" in price:
            return price
        return {"current_price_rub": price}