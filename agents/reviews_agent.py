# Файл: agents/reviews_agent.py
from utils.marketplace_api import get_wb_reviews

class ReviewsAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        print(" - ReviewsAgent (сборщик) инициализирован.")

    def analyze(self, nm_id: int) -> dict:
        """Запрашивает и анализирует отзывы для конкретного nmId."""
        print(f"   [ReviewsAgent]: Анализ отзывов для nmId {nm_id}...")
        
        reviews_data = get_wb_reviews(self.api_key, nm_id)
        if "error" in reviews_data:
            return reviews_data

        total = len(reviews_data)
        avg_rating = sum(r.get("productValuation", 0) for r in reviews_data) / total if total else 0
        
        return {
    "reviews_total": total,
    "average_rating": round(avg_rating, 2),
    "five_star_count": sum(1 for r in reviews_data if r.get("productValuation") == 5),
    "recent_negative": [r for r in reviews_data if r.get("productValuation", 0) <= 3][:3]
}
