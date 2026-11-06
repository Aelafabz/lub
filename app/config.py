import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/lub_auction")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
