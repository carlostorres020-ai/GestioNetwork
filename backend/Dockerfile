# Usar una imagen oficial de Python ligera basada en Alpine Linux
FROM python:3.11-alpine

# Configurar variables de entorno para optimizar Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar ciertas librerías (como criptografía y redes)
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    make \
    iputils

# Copiar el archivo de requerimientos primero para aprovechar la caché de Docker
COPY requirements.txt /app/

# Instalar las librerías de Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar todo el contenido de la carpeta backend local hacia el contenedor
COPY . /app/

# Exponer el puerto interno en el que correrá Uvicorn
EXPOSE 8000

# Comando por defecto para iniciar la aplicación en modo desarrollo asíncrono
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
