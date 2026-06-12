from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
import logging
from database.db import Database
from handlers.utils import check_subscription, get_subscription_keyboard, get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)

try:
    db = Database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    db = None

@router.message(Command("start"))
async def start_command(message: Message):
    """أمر البداية"""
    try:
        if not db:
            await message.answer("❌ عذراً، البوت قيد الصيانة حالياً. يرجى المحاولة لاحقاً.")
            return
        
        user = message.from_user
        
        # إضافة المستخدم إلى قاعدة البيانات
        db.add_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # التحقق من الاشتراك
        is_subscribed = await check_subscription(message.bot, user.id)
        
        if not is_subscribed:
            welcome_text = (
                f"👋 أهلاً بك {user.first_name}!\n\n"
                "🤖 أنا بوت تحرير ملفات PDF المتطور\n\n"
                "⚠️ للاستفادة من خدماتي، يجب عليك الاشتراك في قناتنا أولاً\n\n"
                "📢 بعد الاشتراك، اضغط على زر 'تحقق من الاشتراك'"
            )
            await message.answer(welcome_text, reply_markup=get_subscription_keyboard())
        else:
            welcome_text = (
                f"👋 أهلاً بك {user.first_name}!\n\n"
                "✅ اشتراكك مفعل\n\n"
                "📋 يمكنك استخدام الأزرار أدناه لتحرير ملفات PDF:"
            )
            await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
    
    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        await message.answer("❌ حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.")
