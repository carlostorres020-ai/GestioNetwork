import asyncio
from app.database.session import engine
from app.models.psql_models import Base

async def init_tables():
    print("[+] Conectando y creando tablas en la base de datos...")
    async with engine.begin() as conn:
        # Esto crea todas las tablas definidas bajo 'Base'
        await conn.run_sync(Base.metadata.create_all)
    print("[+] ¡Tablas creadas exitosamente!")

if __name__ == "__main__":
    asyncio.run(init_tables())
