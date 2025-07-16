# Файл: llm/generator.py (ФИНАЛЬНАЯ ГИБРИДНАЯ ВЕРСИЯ)
import json
from gigachat import GigaChat
from config import GIGACHAT_CREDENTIALS
from typing import Dict, Any

# --- ЧАСТЬ 1: ВСПОМОГАТЕЛЬНЫЕ ИНСТРУМЕНТЫ ---

# Эта функция остается для создания клиента GigaChat
if not GIGACHAT_CREDENTIALS:
    giga_client = None
else:
    try:
        giga_client = GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False, temperature=0.01)
    except Exception as e:
        giga_client = None

def _calculate_dynamic(current, previous) -> Dict[str, Any]:
    """Маленький калькулятор для расчета динамики в цифрах и процентах."""
    if previous is None or current is None: return {"abs": "N/A", "perc": "N/A"}
    try:
        absolute_delta = current - previous
        percent_delta = ((current / previous) - 1) * 100 if previous != 0 else 100.0
    except (TypeError, ZeroDivisionError):
        return {"abs": "N/A", "perc": "N/A"}
    return {"abs": round(absolute_delta, 2), "perc": round(percent_delta, 1)}

# --- ЧАСТЬ 2: ГЛАВНАЯ ФУНКЦИЯ ---

def generate_hybrid_report(raw_data: dict, period_1: dict, period_2: dict) -> str:
    """
    Основная функция, которая создает гибридный отчет:
    1. Собирает детальные данные по Периоду 1.
    2. Строит Markdown-таблицу для сравнения.
    3. Отправляет всё в LLM за финальными выводами.
    """
    if not giga_client: return "LLM генератор не активен."

    sku = list(raw_data.keys())[0]
    sku_data = raw_data.get(sku, {})
    if "error" in sku_data: return f"### Анализ для {sku} не удался."

    # --- ШАГ 2.1: Собираем детальные метрики для ОСНОВНОГО периода (Period 1) ---
    p1_metrics = {}
    if sales := sku_data.get('sales', {}).get('period_1', {}): p1_metrics.update(sales)
    if profit := sku_data.get('profit', {}): p1_metrics.update(profit)
    if card := sku_data.get('card', {}): p1_metrics.update(card)
    if reviews := sku_data.get('reviews', {}): p1_metrics.update(reviews)

    # --- ШАГ 2.2: Строим сравнительную таблицу ---
    p1_sales = sku_data.get('sales', {}).get('period_1', {})
    p2_sales = sku_data.get('sales', {}).get('period_2', {})
    
    table_data = {
        "Заказано, шт": (p1_sales.get('units_ordered'), p2_sales.get('units_ordered')),
        "Выручка (общая), руб": (p1_sales.get('gross_revenue_rub'), p2_sales.get('gross_revenue_rub')),
    }
    
    p1_info = f"Период 1 ({period_1['date_from']} - {period_1['date_to']})"
    p2_info = f"Период 2 ({period_2['date_from']} - {period_2['date_to']})"
    
    header = f"| Показатель | {p1_info} | {p2_info} | Динамика (Δ) |\n"
    separator = "|:---|---:|---:|:---|\n"
    body = ""
    for name, (p1_val, p2_val) in table_data.items():
        dynamic = _calculate_dynamic(p1_val, p2_val)
        dynamic_str = f"{dynamic['abs']:+} ({dynamic['perc']:+}%)" if dynamic['abs'] != "N/A" else "N/A"
        body += f"| {name} | {p1_val or 'N/A'} | {p2_val or 'N/A'} | {dynamic_str} |\n"
    comparison_table = header + separator + body

    # --- ШАГ 2.3: Формируем финальный промпт для LLM ---
    prompt = f"""
    Ты — ведущий аналитик маркетплейсов. Твоя задача — написать отчет для руководителя, используя предоставленные данные.

    **ПРАВИЛА:**
    1.  Заполни детальный отчет по основному периоду, используя **ТОЛЬКО** данные из блока "ДЕТАЛЬНЫЕ МЕТРИКИ".
    2.  Вставь готовую **СРАВНИТЕЛЬНУЮ ТАБЛИЦУ** в соответствующий раздел.
    3.  В разделе "Ключевые выводы" напиши свою экспертную оценку, **объединяя** информацию из детального отчета и таблицы. Объясни, что означает динамика в таблице. Дай 1-2 конкретные рекомендации.

    **ШАБЛОН ОТЧЕТА:**
    ---
    ### Аналитический отчет: {sku}
    
    #### 1. Детальные показатели за период ({p1_info})
    - **Название:** `{p1_metrics.get('name', 'нет данных')}`
    - **Цена со скидкой:** `{p1_metrics.get('sale_price_rub', 'нет данных')} руб.`
    - **Остаток:** `{p1_metrics.get('stock_quantity', 'нет данных')} шт.`
    - **Заказано:** `{p1_metrics.get('units_ordered', 'нет данных')} шт.`
    - **Выручка (к перечислению):** `{p1_metrics.get('net_revenue_rub', 'нет данных')} руб.`
    - **Прибыль:** `{p1_metrics.get('profit_rub', 'нет данных')} руб.`
    - **Рейтинг:** `{p1_metrics.get('average_rating', 'N/A')}` (на основе `{p1_metrics.get('total_reviews', 0)}` отзывов)

    #### 2. Сравнение периодов
    {comparison_table}

    #### 3. Ключевые выводы и рекомендации
    [Здесь твой аналитический текст]
    ---
    
    **ДАННЫЕ ДЛЯ ЗАПОЛНЕНИЯ РАЗДЕЛА 1 (ДЕТАЛЬНЫЕ МЕТРИКИ):**
    ```json
    {json.dumps(p1_metrics, indent=2, ensure_ascii=False)}
    ```
    """
    
    try:
        response = giga_client.chat(prompt)
        return response.choices[0].message.content
    except Exception as e:
        return f"Произошла ошибка при генерации отчета: {e}"

# --- ЧАСТЬ 3: СТАРАЯ ФУНКЦИЯ ДЛЯ УТОЧНЯЮЩИХ ВОПРОСОВ ---
# Мы ее оставляем, она нам понадобится для следующего этапа - интерактивности

def answer_question(raw_data_for_aspect: dict, aspect_name: str, sku: str) -> str:
    if not giga_client: return "LLM генератор не активен."
    formatted_data = json.dumps(raw_data_for_aspect, indent=2, ensure_ascii=False)
    prompt = f"Ты — data-аналитик. Объясни кратко и по сути данные по аспекту '{aspect_name}' для товара '{sku}'.\nДанные:\n{formatted_data}"
    try:
        response = giga_client.chat(prompt)
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"