FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y forzar stdout sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias de sistema si es necesario
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el codigo fuente completo
COPY . .

# Puerto expuesto para el Dashboard
EXPOSE 10000

# Comando de inicio del servidor y bots
CMD ["python", "app.py"]
