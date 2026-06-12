from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database
from handlers.utils import check_subscription, get_subscription_keyboard, get_main_menu_keyboard

router = Router()
db = Database()

@router.message(Command("start"))
async def start_command(message: Message):
    """أمر البداية"""
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
            "📋 يمكنك استخدام الأزرار أدناه لتحرير ملفات PDF:\n"
            "• 📑 دمج عدة ملفات PDF\n"
            "• ✂️ تقسيم ملف PDF\n"
            "• 🗑️ حذف صفحات محددة\n"
            "• 📄 استخراج صفحات\n"
            "• 🔄 تدوير الصفحات\n"
            "• 🔀 إعادة ترتيب الصفحات\n"
            "• 📦 ضغط حجم الملف\n"
            "• 🖼️ تحويل الصور إلى PDF\n"
            "• 📸 تحويل PDF إلى صور\n"
            "• 💧 إضافة علامة مائية\n"
            "• 🔒 إضافة كلمة مرور\n"
            "• 🔓 إزالة كلمة مرور\n"
            "• 📝 استخراج النصوص\n"
            "• ℹ️ معلومات الملف"
        )
        await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
