import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, TEMP_DIR
from handlers import routers

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# إنشاء مجلد الملفات المؤقتة
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

async def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    # إنشاء البوت
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # إنشاء الموزع مع تخزين مؤقت
    dp = Dispatcher(storage=MemoryStorage())
    
    # تسجيل الموجهات
    for router in routers:
        dp.include_router(router)
    
    # حذف webhook وبدء البولينج
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("Starting bot...")
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
