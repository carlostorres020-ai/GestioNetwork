import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Obtener la URL de la base de datos desde las variables de entorno (.env)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("ERROR CRÍTICO: La variable DATABASE_URL no está configurada en el archivo .env")

# 2. Crear el motor de conexión asíncrono optimizado para PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True  
)

# 3. Configurar la fábrica de sesiones asíncronas
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 4. Clase base para mapear los modelos declarativos de SQLAlchemy
Base = declarative_base()

# 5. Dependencia para inyectar la sesión de base de datos en las rutas de FastAPI
async def get_db():
    """
    Generador asíncrono para abrir y cerrar de forma segura las sesiones de la BD
    en cada petición, garantizando el aislamiento de transacciones.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
