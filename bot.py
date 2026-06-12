import asyncio
import logging
import os
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# استيراد الإعدادات
sys.path.append(str(Path(__file__).parent))

from config import BOT_TOKEN, TEMP_DIR, WEBHOOK_URL, WEBHOOK_PATH
from database.db import Database
from handlers import routers

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# إنشاء مجلد الملفات المؤقتة
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, exist_ok=True)

# تهيئة قاعدة البيانات
db = Database()

async def on_startup(bot: Bot):
    """تنفيذ عند بدء التشغيل"""
    logger.info("Bot is starting...")
    
    # إعداد webhook إذا كان متاحاً
    if WEBHOOK_URL:
        await bot.set_webhook(
            f"{WEBHOOK_URL}{WEBHOOK_PATH}",
            drop_pending_updates=True
        )
        logger.info(f"Webhook set to {WEBHOOK_URL}{WEBHOOK_PATH}")
    
    logger.info("Bot started successfully!")

async def on_shutdown(bot: Bot):
    """تنفيذ عند إيقاف التشغيل"""
    logger.info("Bot is shutting down...")
    
    # حذف webhook
    if WEBHOOK_URL:
        await bot.delete_webhook()
    
    # إغلاق الجلسات
    await bot.session.close()
    
    logger.info("Bot stopped!")

def create_bot() -> Bot:
    """إنشاء كائن البوت"""
    return Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

def create_dispatcher() -> Dispatcher:
    """إنشاء الموزع مع الموجهات"""
    dp = Dispatcher(storage=MemoryStorage())
    
    # تسجيل جميع الموجهات
    for router in routers:
        dp.include_router(router)
    
    return dp

async def main():
    """الدالة الرئيسية"""
    
    # إنشاء البوت والموزع
    bot = create_bot()
    dp = create_dispatcher()
    
    # تسجيل دوال البدء والإيقاف
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # تشغيل البوت
    try:
        if WEBHOOK_URL:
            # تشغيل مع webhook (لـ Railway)
            app = web.Application()
            
            webhook_requests_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
            )
            
            webhook_requests_handler.register(app, path=WEBHOOK_PATH)
            setup_application(app, dp, bot=bot)
            
            # تشغيل الخادم
            runner = web.AppRunner(app)
            await runner.setup()
            
            port = int(os.getenv("PORT", 8000))
            site = web.TCPSite(runner, host="0.0.0.0", port=port)
            
            logger.info(f"Starting webhook server on port {port}")
            await site.start()
            
            # الانتظار للأبد
            await asyncio.Event().wait()
        else:
            # تشغيل مع polling (للتطوير المحلي)
            logger.info("Starting polling mode...")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
