# Файл: cli_client.py
import requests
import argparse
import json

# Адрес, по которому запущен наш FastAPI сервер
API_BASE_URL = "http://127.0.0.1:8000"

def handle_list_products(args):
    """Обрабатывает команду 'list': запрашивает и выводит список товаров."""
    print("-> Запрашиваю список всех товаров с сервера...")
    try:
        response = requests.get(f"{API_BASE_URL}/products")
        response.raise_for_status()  # Вызовет ошибку, если статус не 200 OK

        data = response.json()
        if "products" in data and data["products"]:
            print(f"✅ Успешно получено {len(data['products'])} товаров:")
            # Выводим краткую информацию по каждому товару
            for i, product in enumerate(data["products"], 1):
                sku = product.get('supplierArticle', 'N/A')
                name = product.get('name', 'Без названия')
                nm_id = product.get('nmId', 'N/A')
                print(f"  {i}. Артикул (SKU): {sku:<25} | ID (nmId): {nm_id:<15} | Название: {name}")
        else:
            print("⚠️ Товары не найдены или получен пустой ответ.")

    except requests.RequestException as e:
        print(f"❌ Ошибка подключения к серверу: {e}")
        print("💡 Убедитесь, что FastAPI сервер запущен командой 'uvicorn main:app --reload'")


def handle_analyze(args):
    """Обрабатывает команду 'analyze': формирует и отправляет запрос на анализ."""
    print("-> Формирую запрос на анализ...")
    
    sku_list_payload = "all" if "all" in args.sku else args.sku
    
    # --- БОЛЕЕ НАДЕЖНАЯ ЛОГИКА ОБРАБОТКИ СЕБЕСТОИМОСТИ ---
    cost_prices_payload = {}
    if args.cost:
        print(f"   - Обработка аргументов себестоимости: {args.cost}")
        for item in args.cost:
            parts = item.split(':')
            if len(parts) != 2:
                print(f"❌ Ошибка: Неверный формат в '{item}'. Пропущен или лишний символ ':'. Используйте 'АРТИКУЛ:ЦЕНА'.")
                return
            
            sku, price_str = parts
            if not sku or not price_str:
                print(f"❌ Ошибка: В паре '{item}' артикул или цена пустые.")
                return

            try:
                price_float = float(price_str)
                cost_prices_payload[sku] = price_float
            except ValueError:
                print(f"❌ Ошибка: Не удалось преобразовать цену '{price_str}' в число для артикула '{sku}'. Убедитесь, что используете точку '.' в качестве десятичного разделителя.")
                return
    
    # --- Формируем итоговый payload ---
    payload = {
        "marketplace": args.marketplace,
        "period_1": {
            "date_from": args.p1_from,
            "date_to": args.p1_to
        },
        "period_2": {
            "date_from": args.p2_from,
            "date_to": args.p2_to
        },
        "sku_list": sku_list_payload,
        "cost_prices": cost_prices_payload
    }
    
    print(f"   - Маркетплейс: {payload['marketplace']}")
    print(f"   - Период 1: с {payload['period_1']['date_from']} по {payload['period_1']['date_to']}")
    print(f"   - Период 2: с {payload['period_2']['date_from']} по {payload['period_2']['date_to']}")
    print(f"   - Товары (SKU): {payload['sku_list']}")
    if payload['cost_prices']:
        print(f"   - Переданные себестоимости: {payload['cost_prices']}")
    
    print("\n-> Отправляю запрос на сервер... (Это может занять некоторое время)")
    
    try:
        response = requests.post(f"{API_BASE_URL}/analyze", json=payload)
        response.raise_for_status()

        data = response.json()
        
        print("\n" + "="*50)
        print("✅ АНАЛИТИЧЕСКИЙ ОТЧЕТ УСПЕШНО ПОЛУЧЕН")
        print("="*50 + "\n")
        
        print(data.get("llm_summary", "Текстовый отчет не был сгенерирован."))
        
        print("\n" + "="*50)
        print("💡 Полные 'сырые' данные (raw_data) также получены.")

    except requests.RequestException as e:
        print(f"❌ Ошибка: {e}")
        try:
            details = e.response.json()
            print(f"   Детали от сервера: {details.get('detail', e.response.text)}")
        except (AttributeError, json.JSONDecodeError):
            pass
        print("\n💡 Убедитесь, что FastAPI сервер запущен и работает без ошибок.")

def main():
    """Основная функция, настраивающая и запускающая парсер команд."""
    parser = argparse.ArgumentParser(
        description="CLI-клиент для мультиагентной аналитической системы."
    )
    
    # Создаем субпарсеры для разных команд (list, analyze)
    subparsers = parser.add_subparsers(dest="command", required=True, help="Доступные команды")

    # --- Команда 'list' ---
    parser_list = subparsers.add_parser("list", help="Получить список всех товаров с маркетплейса.")
    parser_list.set_defaults(func=handle_list_products)

    # --- Команда 'analyze' ---
    parser_analyze = subparsers.add_parser("analyze", help="Запустить анализ для указанных товаров.")
    parser_analyze.add_argument(
        "--sku",
        nargs='+',  # Позволяет принимать один или несколько аргументов
        required=True,
        help='Список артикулов (SKU) для анализа, разделенных пробелом, или слово "all" для анализа всех товаров.'
    )
    # Аргументы для Периода 1
    parser_analyze.add_argument("--p1-from", required=True, help="Дата начала Периода 1 (YYYY-MM-DD)")
    parser_analyze.add_argument("--p1-to", required=True, help="Дата окончания Периода 1 (YYYY-MM-DD)")
    
    # Аргументы для Периода 2 (для сравнения)
    parser_analyze.add_argument("--p2-from", required=True, help="Дата начала Периода 2 (YYYY-MM-DD)")
    parser_analyze.add_argument("--p2-to", required=True, help="Дата окончания Периода 2 (YYYY-MM-DD)")

    parser_analyze.add_argument(
        "--marketplace",
        default="wildberries",
        help="Название маркетплейса (по умолчанию: 'wildberries')."
    )
    parser_analyze.add_argument(
        "--cost",
        nargs='*',
        help="Указать себестоимость. Формат: 'АРТИКУЛ1:ЦЕНА1' 'АРТИКУЛ2:ЦЕНА2'"
    )
    parser_analyze.set_defaults(func=handle_analyze)

    # Разбираем аргументы, которые ввел пользователь
    args = parser.parse_args()
    # Вызываем соответствующую функцию-обработчик
    args.func(args)

if __name__ == "__main__":
    main()