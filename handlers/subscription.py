from aiogram import Router, types
from aiogram.types import CallbackQuery
from handlers.utils import check_subscription, get_main_menu_keyboard

router = Router()

@router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    """التحقق من الاشتراك"""
    user_id = callback.from_user.id
    
    is_subscribed = await check_subscription(callback.bot, user_id)
    
    if is_subscribed:
        await callback.message.edit_text(
            "✅ تم التحقق من اشتراكك بنجاح!\n\n"
            "🎉 يمكنك الآن استخدام جميع ميزات البوت",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.answer(
            "❌ لم تشترك في القناة بعد!\n"
            "يرجى الاشتراك ثم المحاولة مرة أخرى",
            show_alert=True
        )
    
    await callback.answer()

@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """العودة إلى القائمة الرئيسية"""
    await callback.message.edit_text(
        "📋 القائمة الرئيسية\nاختر العملية التي تريد تنفيذها:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
