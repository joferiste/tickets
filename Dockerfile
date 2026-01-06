# Se usará Python 3.12.8 que es con el que se desarrolló el software como base
FROM python:3.12.8-slim

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL y Pillow
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY sistema_boleta/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar el proyecto completo
COPY sistema_boleta/ /app/src/

# Copiar script de entrada
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Crear carpeta de logs
RUN mkdir -p /app/logs /app/media

# Crear directorio para archivos estáticos
RUN mkdir -p /app/staticfiles

# Exponer puerto 8000
EXPOSE 8000

# Ejecutar el script de entrada
ENTRYPOINT [ "/app/entrypoint.sh" ]