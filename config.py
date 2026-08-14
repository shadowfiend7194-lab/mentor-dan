import os
from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "dan.db"
)

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
)


if not BOT_TOKEN:
    raise ValueError(
        "❌ BOT_TOKEN не найден в .env"
    )