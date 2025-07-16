# Файл: config.py
import os
from dotenv import load_dotenv

# Эта команда загружает переменные из файла .env в окружение нашего приложения
load_dotenv()

# Читаем ключ из переменных окружения
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
MARKETPLACE_API_KEY = os.getenv("MARKETPLACE_API_KEY")

# Проверка, что ключ успешно загружен
if not GIGACHAT_CREDENTIALS:
    print("ПРЕДУПРЕЖДЕНИЕ: Ключ GIGACHAT_CREDENTIALS не найден...")