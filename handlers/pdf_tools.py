import os
import asyncio
from io import BytesIO
from typing import List
import PyPDF2
import fitz  # pymupdf
from PIL import Image
import pikepdf
from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.utils import (
    download_file, cleanup_temp_files, format_file_size,
    check_subscription, get_main_menu_keyboard, db
)
from config import MAX_FILE_SIZE, TEMP_DIR

router = Router()

# حالات FSM للعمليات المختلفة
class PDFStates(StatesGroup):
    waiting_for_merge_files = State()
    waiting_for_split = State()
    waiting_for_delete_pages = State()
    waiting_for_extract_pages = State()
    waiting_for_rotate = State()
    waiting_for_reorder = State()
    waiting_for_compress = State()
    waiting_for_images = State()
    waiting_for_pdf_to_images = State()
    waiting_for_watermark = State()
    waiting_for_add_password = State()
    waiting_for_remove_password = State()
    waiting_for_file_info = State()

async def verify_subscription(callback_or_message):
    """التحقق من الاشتراك قبل تنفيذ أي عملية"""
    user_id = callback_or_message.from_user.id
    
    # التحقق من الحظر
    if db.is_banned(user_id):
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.answer("❌ أنت محظور من استخدام البوت", show_alert=True)
        else:
            await callback_or_message.answer("❌ أنت محظور من استخدام البوت")
        return False
    
    is_subscribed = await check_subscription(callback_or_message.bot, user_id)
    if not is_subscribed:
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.answer(
                "❌ يجب الاشتراك في القناة أولاً!\n@BEXO50",
                show_alert=True
            )
        else:
            await callback_or_message.answer(
                "❌ يجب الاشتراك في القناة أولاً!\n@BEXO50"
            )
        return False
    
    return True

@router.callback_query(lambda c: c.data == "merge_pdf")
async def merge_pdf_start(callback: CallbackQuery, state: FSMContext):
    """بدء عملية دمج PDF"""
    if not await verify_subscription(callback):
        return
    
    await callback.message.edit_text(
        "📑 دمج ملفات PDF\n\n"
        "أرسل جميع ملفات PDF التي تريد دمجها دفعة واحدة.\n"
        "سيتم دمجها بالترتيب الذي ترسله به.\n\n"
        "⚠️ الحد الأقصى للحجم الإجمالي: 50 ميجابايت"
    )
    await state.set_state(PDFStates.waiting_for_merge_files)
    await callback.answer()

@router.message(PDFStates.waiting_for_merge_files, F.document)
async def process_merge_pdf(message: Message, state: FSMContext):
    """معالجة دمج ملفات PDF"""
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ يرجى إرسال ملفات PDF فقط!")
        return
    
    data = await state.get_data()
    files = data.get('files', [])
    
    # تحميل الملف
    file_path = await download_file(
        message, message.bot,
        message.document.file_id,
        f"merge_{len(files)}_{message.document.file_name}"
    )
    files.append(file_path)
    await state.update_data(files=files)
    
    await message.answer(
        f"✅ تم استلام الملف ({len(files)})\n"
        "أرسل المزيد من الملفات أو اضغط /done للبدء في الدمج\n"
        "أو /cancel للإلغاء"
    )

@router.message(PDFStates.waiting_for_merge_files, F.text == "/done")
async def finish_merge_pdf(message: Message, state: FSMContext):
    """إنهاء عملية الدمج والبدء في الدمج"""
    data = await state.get_data()
    files = data.get('files', [])
    
    if len(files) < 2:
        await message.answer("❌ يجب إرسال ملفين على الأقل للدمج!")
        return
    
    # التحقق من الحجم الإجمالي
    total_size = sum(os.path.getsize(f) for f in files)
    if total_size > 50 * 1024 * 1024:  # 50MB
        await message.answer("❌ الحجم الإجمالي للملفات كبير جداً (الحد الأقصى 50 ميجابايت)")
        cleanup_temp_files(*files)
        await state.clear()
        return
    
    status_msg = await message.answer("⏳ جاري دمج الملفات...")
    
    try:
        # دمج الملفات
        merger = PyPDF2.PdfMerger()
        for file in files:
            merger.append(file)
        
        output_path = f"{TEMP_DIR}/merged_{message.from_user.id}.pdf"
        merger.write(output_path)
        merger.close()
        
        # إرسال الملف المدمج
        await message.answer_document(
            FSInputFile(output_path),
            caption="✅ تم دمج الملفات بنجاح!"
        )
        
        # تسجيل الإحصائية
        db.add_usage_stat(message.from_user.id, "merge", total_size)
        
        # تنظيف الملفات
        cleanup_temp_files(*files, output_path)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء الدمج: {str(e)}")
        cleanup_temp_files(*files)
    
    await state.clear()

@router.message(PDFStates.waiting_for_merge_files, F.text == "/cancel")
async def cancel_merge(message: Message, state: FSMContext):
    """إلغاء عملية الدمج"""
    data = await state.get_data()
    files = data.get('files', [])
    cleanup_temp_files(*files)
    await state.clear()
    await message.answer("❌ تم إلغاء عملية الدمج", reply_markup=get_main_menu_keyboard())

@router.callback_query(lambda c: c.data == "compress_pdf")
async def compress_pdf_start(callback: CallbackQuery, state: FSMContext):
    """بدء عملية ضغط PDF"""
    if not await verify_subscription(callback):
        return
    
    await callback.message.edit_text(
        "📦 ضغط ملف PDF\n\n"
        "أرسل ملف PDF الذي تريد ضغطه.\n"
        "سيتم تقليل حجم الملف مع الحفاظ على الجودة."
    )
    await state.set_state(PDFStates.waiting_for_compress)
    await callback.answer()

@router.message(PDFStates.waiting_for_compress, F.document)
async def process_compress_pdf(message: Message, state: FSMContext):
    """معالجة ضغط PDF"""
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ يرجى إرسال ملف PDF فقط!")
        return
    
    if message.document.file_size > MAX_FILE_SIZE:
        await message.answer(f"❌ حجم الملف كبير جداً (الحد الأقصى {format_file_size(MAX_FILE_SIZE)})")
        return
    
    status_msg = await message.answer("⏳ جاري ضغط الملف...")
    
    try:
        # تحميل الملف
        file_path = await download_file(
            message, message.bot,
            message.document.file_id,
            f"compress_{message.from_user.id}.pdf"
        )
        
        # ضغط الملف باستخدام pikepdf
        output_path = f"{TEMP_DIR}/compressed_{message.from_user.id}.pdf"
        
        pdf = pikepdf.Pdf.open(file_path)
        pdf.save(output_path, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        pdf.close()
        
        # مقارنة الأحجام
        original_size = os.path.getsize(file_path)
        compressed_size = os.path.getsize(output_path)
        reduction = ((original_size - compressed_size) / original_size) * 100
        
        caption = (
            f"✅ تم ضغط الملف بنجاح!\n\n"
            f"📊 إحصائيات الضغط:\n"
            f"• الحجم الأصلي: {format_file_size(original_size)}\n"
            f"• الحجم بعد الضغط: {format_file_size(compressed_size)}\n"
            f"• نسبة التوفير: {reduction:.1f}%"
        )
        
        await message.answer_document(
            FSInputFile(output_path),
            caption=caption
        )
        
        db.add_usage_stat(message.from_user.id, "compress", original_size)
        
        cleanup_temp_files(file_path, output_path)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء الضغط: {str(e)}")
    
    await state.clear()

@router.callback_query(lambda c: c.data == "pdf_to_images")
async def pdf_to_images_start(callback: CallbackQuery, state: FSMContext):
    """بدء تحويل PDF إلى صور"""
    if not await verify_subscription(callback):
        return
    
    await callback.message.edit_text(
        "📸 تحويل PDF إلى صور\n\n"
        "أرسل ملف PDF لتحويله إلى صور.\n"
        "سيتم إنشاء صورة لكل صفحة."
    )
    await state.set_state(PDFStates.waiting_for_pdf_to_images)
    await callback.answer()

@router.message(PDFStates.waiting_for_pdf_to_images, F.document)
async def process_pdf_to_images(message: Message, state: FSMContext):
    """تحويل PDF إلى صور"""
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ يرجى إرسال ملف PDF فقط!")
        return
    
    status_msg = await message.answer("⏳ جاري تحويل PDF إلى صور...")
    
    try:
        file_path = await download_file(
            message, message.bot,
            message.document.file_id,
            f"to_images_{message.from_user.id}.pdf"
        )
        
        # فتح PDF باستخدام pymupdf
        pdf_document = fitz.open(file_path)
        total_pages = len(pdf_document)
        
        if total_pages > 20:
            await status_msg.edit_text("❌ عدد الصفحات كبير جداً (الحد الأقصى 20 صفحة)")
            pdf_document.close()
            cleanup_temp_files(file_path)
            await state.clear()
            return
        
        await status_msg.edit_text(f"⏳ جاري تحويل {total_pages} صفحات...")
        
        # تحويل كل صفحة إلى صورة
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            # تحويل الصفحة إلى صورة
            pix = page.get_pixmap(dpi=150)
            img_path = f"{TEMP_DIR}/page_{page_num + 1}_{message.from_user.id}.png"
            pix.save(img_path)
            
            await message.answer_document(
                FSInputFile(img_path),
                caption=f"📄 صفحة {page_num + 1} من {total_pages}"
            )
            
            cleanup_temp_files(img_path)
            
            if page_num < total_pages - 1:
                await asyncio.sleep(1)  # تجنب تجاوز حد المعدل
        
        pdf_document.close()
        await status_msg.edit_text(f"✅ تم تحويل {total_pages} صفحات بنجاح!")
        
        db.add_usage_stat(message.from_user.id, "pdf_to_images", os.path.getsize(file_path))
        cleanup_temp_files(file_path)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ: {str(e)}")
        if 'file_path' in locals():
            cleanup_temp_files(file_path)
    
    await state.clear()

@router.callback_query(lambda c: c.data == "extract_text")
async def extract_text_start(callback: CallbackQuery, state: FSMContext):
    """بدء استخراج النص من PDF"""
    if not await verify_subscription(callback):
        return
    
    await callback.message.edit_text(
        "📝 استخراج النص من PDF\n\n"
        "أرسل ملف PDF لاستخراج النص منه."
    )
    await state.set_state(PDFStates.waiting_for_extract_pages)
    await callback.answer()

@router.message(PDFStates.waiting_for_extract_pages, F.document)
async def process_extract_text(message: Message, state: FSMContext):
    """استخراج النص من PDF"""
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ يرجى إرسال ملف PDF فقط!")
        return
    
    status_msg = await message.answer("⏳ جاري استخراج النص...")
    
    try:
        file_path = await download_file(
            message, message.bot,
            message.document.file_id,
            f"extract_{message.from_user.id}.pdf"
        )
        
        # استخراج النص باستخدام pymupdf
        pdf_document = fitz.open(file_path)
        total_pages = len(pdf_document)
        
        text_content = []
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            text = page.get_text()
            if text.strip():
                text_content.append(f"--- صفحة {page_num + 1} ---\n{text}")
        
        pdf_document.close()
        
        if text_content:
            full_text = "\n\n".join(text_content)
            
            # إذا كان النص طويلاً، حفظه كملف
            if len(full_text) > 3500:
                text_path = f"{TEMP_DIR}/text_{message.from_user.id}.txt"
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                
                await message.answer_document(
                    FSInputFile(text_path),
                    caption=f"✅ تم استخراج النص من {total_pages} صفحات"
                )
                cleanup_temp_files(text_path)
            else:
                await message.answer(f"📝 النص المستخرج:\n\n{full_text}")
        else:
            await message.answer("❌ لا يوجد نص في هذا الملف (قد يكون صوراً ممسوحة ضوئياً)")
        
        await status_msg.delete()
        db.add_usage_stat(message.from_user.id, "extract_text")
        cleanup_temp_files(file_path)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ: {str(e)}")
        if 'file_path' in locals():
            cleanup_temp_files(file_path)
    
    await state.clear()

@router.callback_query(lambda c: c.data == "file_info")
async def file_info_start(callback: CallbackQuery, state: FSMContext):
    """بدء عرض معلومات الملف"""
    if not await verify_subscription(callback):
        return
    
    await callback.message.edit_text(
        "ℹ️ معلومات ملف PDF\n\n"
        "أرسل ملف PDF لعرض معلوماته."
    )
    await state.set_state(PDFStates.waiting_for_file_info)
    await callback.answer()

@router.message(PDFStates.waiting_for_file_info, F.document)
async def process_file_info(message: Message, state: FSMContext):
    """عرض معلومات ملف PDF"""
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ يرجى إرسال ملف PDF فقط!")
        return
    
    try:
        file_path = await download_file(
            message, message.bot,
            message.document.file_id,
            f"info_{message.from_user.id}.pdf"
        )
        
        # قراءة معلومات الملف
        pdf_reader = PyPDF2.PdfReader(file_path)
        metadata = pdf_reader.metadata
        num_pages = len(pdf_reader.pages)
        
        # معلومات إضافية باستخدام pymupdf
        pdf_document = fitz.open(file_path)
        page_sizes = set()
        for page in pdf_document:
            rect = page.rect
            page_sizes.add(f"{rect.width:.0f}x{rect.height:.0f}")
        pdf_document.close()
        
        info_text = (
            f"ℹ️ معلومات الملف\n\n"
            f"📄 اسم الملف: {message.document.file_name}\n"
            f"📏 الحجم: {format_file_size(os.path.getsize(file_path))}\n"
            f"📑 عدد الصفحات: {num_pages}\n"
            f"📐 حجم الصفحات: {', '.join(page_sizes)}\n"
        )
        
        if metadata:
            if metadata.title:
                info_text += f"📝 العنوان: {metadata.title}\n"
            if metadata.author:
                info_text += f"✍️ المؤلف: {metadata.author}\n"
            if metadata.subject:
                info_text += f"📌 الموضوع: {metadata.subject}\n"
            if metadata.creator:
                info_text += f"🔧 برنامج الإنشاء: {metadata.creator}\n"
        
        # التحقق من وجود كلمة مرور
        try:
            pdf_reader.decrypt('')
            info_text += "\n🔓 الملف غير محمي بكلمة مرور"
        except:
            info_text += "\n🔒 الملف محمي بكلمة مرور"
        
        await message.answer(info_text)
        
        db.add_usage_stat(message.from_user.id, "file_info")
        cleanup_temp_files(file_path)
        
    except Exception as e:
        await message.answer(f"❌ حدث خطأ: {str(e)}")
        if 'file_path' in locals():
            cleanup_temp_files(file_path)
    
    await state.clear()

@router.callback_query(lambda c: c.data == "my_stats")
async def show_user_stats(callback: CallbackQuery):
    """عرض إحصائيات المستخدم"""
    if not await verify_subscription(callback):
        return
    
    stats = db.get_stats()
    stats_text = (
        f"📊 إحصائيات البوت\n\n"
        f"👥 إجمالي المستخدمين: {stats['total_users']}\n"
        f"✅ المشتركين: {stats['subscribed_users']}\n"
        f"📈 العمليات اليوم: {stats['total_operations']}\n"
        f"👤 النشطين اليوم: {stats['active_today']}\n"
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
        ])
    )
    await callback.answer()
