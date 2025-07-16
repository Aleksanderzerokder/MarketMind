# Файл: agents/card_agent.py (ФИНАЛЬНАЯ ВЕРСИЯ)
from typing import Dict, Any
from utils.wb_charcs_cache import get_required_charcs

class CardAgent:
    def __init__(self):
        print(" - CardAgent (процессор) инициализирован.")

    def analyze(self, product_card: dict) -> dict:
        if not product_card:
            return {"error": "Product card data not provided"}

        # --- 1. НАДЕЖНОЕ ИЗВЛЕЧЕНИЕ КЛЮЧЕВЫХ ДАННЫХ ---
        product_name = (
            product_card.get('name') or
            product_card.get('title') or
            product_card.get('supplierArticle') or
            "NO_NAME"
        )
        brand = product_card.get('brand') or "нет данных"
        stock = product_card.get("quantity", 0)
        description = product_card.get('description', "")
        
        # --- ФИНАЛЬНЫЙ, УНИВЕРСАЛЬНЫЙ РАСЧЕТ ЦЕН ---
        # Извлекаем базовую цену и скидку
        base_price = float(product_card.get("Price", 0))
        discount_percent = float(product_card.get("Discount", 0))

        # Рассчитываем цену со скидкой
        sale_price = base_price * (1 - discount_percent / 100)
        
        # --- 2. ВАША АНАЛИТИЧЕСКАЯ ЛОГИКА (сохранена) ---
        title_ok = len(product_name) >= 20
        desc_ok = len(description) >= 300
        brand_ok = bool(brand and brand != "нет данных")
        clickbait_ok = any(word in product_name.lower() for word in ['новинка', 'хит', 'подарок', 'premium', 'top', 'выбор', 'лучший', 'original'])
        photos = product_card.get('photos_count', 0)
        videos = product_card.get('videos_count', 0)
        photos_ok = photos >= 5
        videos_ok = videos >= 1
        
        subject_id = product_card.get("subjectID") or product_card.get("subjectId")
        required = get_required_charcs(subject_id) if subject_id else set()
        present = set(attr.get("name") for attr in product_card.get("characteristics", []))
        missing = required - present if required else set()

        sale_ok = discount_percent > 0

        # Формирование рекомендаций (ваша логика полностью сохранена)
        recommendations = []
        if not brand_ok:
            recommendations.append("Заполните поле 'Бренд' — это повышает доверие покупателей.")
        if not title_ok:
            recommendations.append("Удлините название до 20+ символов, добавив ключевые слова.")
        if not clickbait_ok:
            recommendations.append("Добавьте в название УТП или триггеры ('новинка', 'хит', 'подарок', 'лучший' и т.п.).")
        if not desc_ok:
            recommendations.append("Добавьте подробное описание (не менее 300 символов), сделайте акцент на выгодах и сценариях применения.")
        if not photos_ok:
            recommendations.append("Добавьте минимум 5 качественных фотографий (в т.ч. 'лайфстайл', упаковку, состав, использование).")
        if not videos_ok:
            recommendations.append("Загрузите хотя бы одно видео для повышения доверия и кликабельности.")
        if missing:
            recommendations.append(f"Заполните обязательные атрибуты: {', '.join(missing)}.")
        if not sale_ok and discount_percent > 0:
            recommendations.append("Проверьте отображение скидки: цена или скидка указаны некорректно.")
        if not recommendations:
            recommendations.append("Карточка товара оформлена отлично — высокая вероятность хороших продаж!")
        if product_name in [None, "", "NO_NAME", "нет данных"]:
            recommendations.append(
            "Нет информации по карточке товара — вероятно, она создана в старой версии Личного кабинета WB. "
            "Для подробного анализа создайте или обновите карточку в новом Личном кабинете Wildberries."
             )
        if not recommendations:
            recommendations = ["Карточка товара оформлена корректно."]    

        return {
           "name": product_name,
            "brand": brand,
            "base_price_rub": round(base_price, 2),
            "sale_price_rub": round(sale_price, 2),
            "discount_percent": round(discount_percent),
            "current_price_rub": round(sale_price, 2),
            "stock_quantity": stock,
            "warning": product_card.get("warning", ""),
            "recommendations": recommendations,
        }
        