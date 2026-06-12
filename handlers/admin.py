from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS
from database.db import Database

router = Router()
db = Database()

class BroadcastStates(StatesGroup):
    waiting_for_broadcast = State()

def is_admin(user_id: int) -> bool:
    """التحقق من صلاحيات المشرف"""
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """لوحة تحكم المشرف"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للمشرفين فقط")
        return
    
    stats = db.get_stats()
    admin_text = (
        "🔧 لوحة تحكم المشرف\n\n"
        f"📊 إحصائيات سريعة:\n"
        f"👥 المستخدمين: {stats['total_users']}\n"
        f"✅ المشتركين: {stats['subscribed_users']}\n"
        f"📈 العمليات: {stats['total_operations']}\n"
        f"👤 النشطين اليوم: {stats['active_today']}\n\n"
        "الأوامر المتاحة:\n"
        "/stats - إحصائيات مفصلة\n"
        "/broadcast - إرسال رسالة للجميع\n"
        "/ban <user_id> - حظر مستخدم\n"
        "/unban <user_id> - فك حظر مستخدم\n"
        "/users - قائمة آخر 10 مستخدمين"
    )
    
    await message.answer(admin_text)

@router.message(Command("stats"))
async def detailed_stats(message: Message):
    """إحصائيات مفصلة"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للمشرفين فقط")
        return
    
    stats = db.get_stats()
    stats_text = (
        "📊 إحصائيات مفصلة\n\n"
        f"👥 إجمالي المستخدمين: {stats['total_users']}\n"
        f"✅ المستخدمين المشتركين: {stats['subscribed_users']}\n"
        f"❌ غير المشتركين: {stats['total_users'] - stats['subscribed_users']}\n"
        f"📈 إجمالي العمليات: {stats['total_operations']}\n"
        f"👤 المستخدمين النشطين اليوم: {stats['active_today']}\n"
        f"\n📅 {message.date.strftime('%Y-%m-%d %H:%M')}"
    )
    
    await message.answer(stats_text)

@router.message(Command("broadcast"))
async def broadcast_start(message: Message, state: FSMContext):
    """بدء البث الجماعي"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للمشرفين فقط")
        return
    
    await message.answer(
        "📢 إرسال رسالة جماعية\n\n"
        "أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:\n"
        "(يمكنك إرسال نص، صورة، فيديو، أو ملف)\n"
        "/cancel للإلغاء"
    )
    await state.set_state(BroadcastStates.waiting_for_broadcast)

@router.message(BroadcastStates.waiting_for_broadcast)
async def broadcast_send(message: Message, state: FSMContext):
    """إرسال البث الجماعي"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ تم إلغاء البث")
        return
    
    users = db.get_all_users()
    success_count = 0
    fail_count = 0
    
    status_msg = await message.answer("⏳ جاري إرسال البث...")
    
    for user in users:
        try:
            # إعادة توجيه الرسالة لكل مستخدم
            await message.copy_to(chat_id=user.telegram_id)
            success_count += 1
        except Exception:
            fail_count += 1
        
        # تجنب تجاوز حد المعدل
        await asyncio.sleep(0.05)
    
    await status_msg.edit_text(
        f"✅ تم إرسال البث\n\n"
        f"✅ نجح: {success_count}\n"
        f"❌ فشل: {fail_count}"
    )
    
    await state.clear()

@router.message(Command("ban"))
async def ban_user(message: Message):
    """حظر مستخدم"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للمشرفين فقط")
        return
    
    try:
        user_id = int(message.text.split()[1])
        if db.ban_user(user_id):
            await message.answer(f"✅ تم حظر المستخدم {user_id}")
        else:
            await message.answer("❌ لم يتم العثور على المستخدم")
    except (IndexError, ValueError):
        await message.answer("❌ استخدم الأمر هكذا: /ban <user_id>")

@router.message(Command("unban"))
async def unban_user(message: Message):
    """فك حظر مستخدم"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للمشرفين فقط")
        return
    
    try:
        user_id = int(message.text.split()[1])
        if db.unban_user(user_id):
            await message.answer(f"✅ تم فك حظر المستخدم {user_id}")
        else:
            await message.answer("❌ لم يتم العثور على المستخدم")
    except (IndexError, ValueError):
        await message.answer("❌ استخدم الأمر هكذا: /unban <user_id>")

@router.message(Command("users"))
async def list_users(message: Message):
    """قائمة المستخدمين"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للمشرفين فقط")
        return
    
    users = db.get_all_users()[:10]  # آخر 10 مستخدمين
    users_text = "👥 آخر المستخدمين:\n\n"
    
    for user in users:
        status = "✅" if user.is_subscribed else "❌"
        banned = "🚫" if user.is_banned else ""
        users_text += (
            f"{status}{banned} {user.first_name or 'بدون اسم'} "
            f"(@{user.username or 'بدون'})\n"
            f"ID: {user.telegram_id} | عمليات: {user.total_operations}\n\n"
        )
    
    await message.answer(users_text)
