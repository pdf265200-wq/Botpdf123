import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@BEXO50"
CHANNEL_URL = "https://t.me/BEXO50"
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']
MAX_MERGED_SIZE = 50 * 1024 * 1024  # 50MB
TEMP_DIR = "temp"
