FROM python:3.11-slim

WORKDIR /app

# تثبيت الاعتماديات النظامية
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# إنشاء مجلد للملفات المؤقتة
RUN mkdir -p temp

CMD ["python", "bot.py"]
