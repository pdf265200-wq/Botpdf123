import os
import asyncio
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from config import CHANNEL_ID, CHANNEL_URL
from database.db import Database

db = Database()

async def check_subscription(bot, user_id: int) -> bool:
    """التحقق من اشتراك المستخدم في القناة"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_subscribed = member.status not in ['left', 'kicked']
        db.update_subscription(user_id, is_subscribed)
        return is_subscribed
    except Exception:
        return False

def get_subscription_keyboard():
    """الحصول على لوحة أزرار الاشتراك"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 انضم إلى القناة", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ تحقق من الاشتراك", callback_data="check_subscription")]
    ])
    return keyboard

def get_main_menu_keyboard():
    """الحصول على القائمة الرئيسية"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📑 دمج PDF", callback_data="merge_pdf"),
            InlineKeyboardButton(text="✂️ تقسيم PDF", callback_data="split_pdf")
        ],
        [
            InlineKeyboardButton(text="🗑️ حذف صفحات", callback_data="delete_pages"),
            InlineKeyboardButton(text="📄 استخراج صفحات", callback_data="extract_pages")
        ],
        [
            InlineKeyboardButton(text="🔄 تدوير الصفحات", callback_data="rotate_pages"),
            InlineKeyboardButton(text="🔀 إعادة ترتيب", callback_data="reorder_pages")
        ],
        [
            InlineKeyboardButton(text="📦 ضغط PDF", callback_data="compress_pdf"),
            InlineKeyboardButton(text="🖼️ صور إلى PDF", callback_data="images_to_pdf")
        ],
        [
            InlineKeyboardButton(text="📸 PDF إلى صور", callback_data="pdf_to_images"),
            InlineKeyboardButton(text="💧 علامة مائية", callback_data="watermark")
        ],
        [
            InlineKeyboardButton(text="🔒 إضافة كلمة مرور", callback_data="add_password"),
            InlineKeyboardButton(text="🔓 إزالة كلمة مرور", callback_data="remove_password")
        ],
        [
            InlineKeyboardButton(text="📝 استخراج النص", callback_data="extract_text"),
            InlineKeyboardButton(text="ℹ️ معلومات الملف", callback_data="file_info")
        ],
        [
            InlineKeyboardButton(text="📊 إحصائياتي", callback_data="my_stats")
        ]
    ])
    return keyboard

async def download_file(message: Message, bot, file_id: str, filename: str) -> str:
    """تحميل ملف من تيليجرام"""
    file = await bot.get_file(file_id)
    file_path = f"temp/{filename}"
    await bot.download_file(file.file_path, file_path)
    return file_path

def cleanup_temp_files(*files):
    """حذف الملفات المؤقتة"""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception:
            pass

def format_file_size(size_bytes: int) -> str:
    """تنسيق حجم الملف"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"
