import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

# إعدادات webhook لـ Railway
RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if RAILWAY_PUBLIC_DOMAIN:
    WEBHOOK_URL = f"https://{RAILWAY_PUBLIC_DOMAIN}"
    WEBHOOK_PATH = "/webhook"
else:
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")

# إعدادات القناة
CHANNEL_ID = os.getenv("CHANNEL_ID", "@BEXO50")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/BEXO50")

# معرفات المشرفين
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id_str) for id_str in ADMIN_IDS_STR.split(",") if id_str.strip()]

# قاعدة البيانات - استخدام PostgreSQL على Railway إذا كان متاحاً
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    # استخدام SQLite للتطوير المحلي
    DATABASE_URL = os.getenv("DATABASE_URL_LOCAL", "sqlite:///bot_data.db")

# إعدادات الملفات
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "pdf,jpg,jpeg,png").split(",")
MAX_MERGED_SIZE = int(os.getenv("MAX_MERGED_SIZE", 50 * 1024 * 1024))  # 50MB

# مجلد الملفات المؤقتة
TEMP_DIR = Path(os.getenv("TEMP_DIR", "temp"))
