# Imagen base con Python
FROM python:3.11-slim

# Instalar dependencias necesarias del sistema
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libxss1 \
    libasound2 \
    libxshmfence1 \
    libgbm1 \
    wget \
    curl \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Establecer variables para Chromium
ENV CHROMIUM_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader punkt wordnet stopwords && \
    python manage.py migrate && \
    python manage.py collectstatic --noinput

# Exponer puerto si es necesario (cambia 8000 por el tuyo)
EXPOSE 8000

# Comando por defecto para iniciar la app
CMD ["gunicorn", "expansor_de_consultas.wsgi:application", "--bind", "0.0.0.0:8000"]
