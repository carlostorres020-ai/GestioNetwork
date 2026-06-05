import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Configuración de Pydantic v2 para la lectura del entorno
    model_config = ConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # 1. SEGURIDAD Y JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # 2. CONFIGURACIÓN POSTGRESQL + POSTGIS
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    # 3. CONFIGURACIÓN REDIS (TELEMETRÍA)
    REDIS_PASSWORD: str
    REDIS_URL: str

# Instancia global para importar las configuraciones en cualquier parte del sistema
settings = Settings()
