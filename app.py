from fastapi import FastAPI, HTTPException, Body, Query
import asyncio
import os
from dotenv import load_dotenv
from starlette import status
from parser import TGParser

# 1. Загрузка переменных окружения (для локального тестирования)
# На Railway это не нужно, но не повредит, если файл .env есть
load_dotenv()

# 2. Получение и преобразование переменных окружения
# ПРЕДУПРЕЖДЕНИЕ: os.getenv() возвращает строку или None. 
# Если переменная не установлена, int() вызовет ошибку. 
# Это хорошо, потому что заставит вас установить переменные.
try:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    TOKEN = os.getenv("TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    SESSION_NAME = os.getenv("SESSION_NAME")
    DB_PATH = os.getenv("DB_PATH")
    PROXY_IP = os.getenv("PROXY_IP")
    PROXY_PORT = os.getenv("PROXY_PORT")

except TypeError as e:
    print(f"FATAL ERROR: Environment variable is missing or invalid: {e}")
    raise e

# 3. 🔥 ИНИЦИАЛИЗАЦИЯ ГЛОБАЛЬНОГО ОБЪЕКТА TGParser
# Это устраняет NameError: name 'parser' is not defined
try:
    parser = TGParser(
        api_id=API_ID,
        api_hash=API_HASH,
        session_name=SESSION_NAME,
        db_path=DB_PATH,
        webhook_url=WEBHOOK_URL,
        proxy_ip=PROXY_IP,
        proxy_port=PROXY_PORT
    )
except Exception as e:
    print(f"FATAL ERROR: Failed to initialize TGParser: {e}")
    # Если парсер не создался, приложение не должно запускаться
    raise e 

# 4. Создание экземпляра FastAPI
app = FastAPI()


@app.get("/health")
async def health():
    """Проверка состояния сервиса."""
    return {"status": "ok"}


@app.post("/run")
async def run(payload: dict = Body(...), token: str = Query(None)):
    """
    Основная точка входа. Запускает парсер в фоновом режиме.
    """
    # 5. Проверка токена (как параметр запроса)
    if token != TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # 6. Валидация входных данных
    channels = payload.get("channels")
    if not isinstance(channels, list):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Input 'channels' must be a valid list")
    
    # 7. 🔥 ГЛАВНОЕ ИСПРАВЛЕНИЕ: Запуск parser.run в фоновой задаче
    # Используем глобальный объект 'parser' и не блокируем HTTP-ответ
    asyncio.create_task(parser.run(channels))

    return {"status": "started", "message": "Parser job initiated in the background."}
