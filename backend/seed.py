import asyncio
import bcrypt
from app.database.session import AsyncSessionLocal
from app.models.psql_models import Empresa, Usuario
from uuid import uuid4

async def crear_datos_iniciales():
    async with AsyncSessionLocal() as session:
        print("[+] Iniciando siembra (bypass passlib)...")
        
        # Generar hash directamente con la librería bcrypt 5.0.0
        password_bytes = "admin123".encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        empresa = Empresa(
            id=uuid4(),
            nombre_comercial="Gtrack",
            ruc_identificacion="1790000000001",
            correo_contacto="admin@gtrack.net",
            activo=True
        )
        session.add(empresa)
        await session.flush()
        
        usuario = Usuario(
            id=uuid4(),
            empresa_id=empresa.id,
            username="admin_gtrack",
            nombre_completo="Administrador",
            password_hash=hashed,
            rol="administrador",
            activo=True
        )
        session.add(usuario)
        
        await session.commit()
        print("[+] ¡Éxito! Usuario 'admin_gtrack' con password 'admin123' creado.")

if __name__ == "__main__":
    asyncio.run(crear_datos_iniciales())
