FROM python:3.11-slim

WORKDIR /app

# تثبيت الاعتماديات النظامية - متوافق مع Debian Trixie
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpoppler-cpp-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المتطلبات أولاً للاستفادة من التخزين المؤقت
COPY requirements.txt .

# تثبيت الاعتماديات مع تعطيل التخزين المؤقت لتقليل الحجم
RUN pip install --no-cache-dir -r requirements.txt

# نسخ جميع الملفات
COPY . .

# إنشاء مجلد الملفات المؤقتة
RUN mkdir -p temp

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# فتح المنفذ
EXPOSE 8000

# تشغيل البوت
CMD ["python", "bot.py"]
