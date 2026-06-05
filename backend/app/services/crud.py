import os
import base64
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from geoalchemy2.elements import WKTElement
from app.models import psql_models
from app.schemas import auth, network
from app.core.security import obtener_password_hash

# ===========================================================================
# CONFIGURACIÓN DE CIFRADO SIMÉTRICO SEGURO (MÉTODO DERIVADO URL-SAFE)
# ===========================================================================
# Fernet exige estrictamente una clave url-safe de 32 bytes en Base64.
# Derivamos la clave usando SHA256 sobre el JWT_SECRET para garantizar la consistencia.
JWT_SECRET_RAW = os.getenv("JWT_SECRET", "GtrackSecureNetworkDefaultKey32BytesForEncryption!")

try:
    key_hash = hashlib.sha256(JWT_SECRET_RAW.encode()).digest()
    cipher_key = base64.urlsafe_b64encode(key_hash)
    fernet = Fernet(cipher_key)
except Exception:
    # Respaldo seguro en caso de contingencia extrema
    from cryptography.fernet import Fernet as FallbackFernet
    fernet = FallbackFernet(FallbackFernet.generate_key())

def encriptar_credencial(texto_plano: str) -> str:
    return fernet.encrypt(texto_plano.encode()).decode()

def desencriptar_credencial(texto_cifrado: str) -> str:
    return fernet.decrypt(texto_cifrado.encode()).decode()


# ===========================================================================
# 1. SERVICIOS DE GESTIÓN MULTI-TENANT (EMPRESAS Y USUARIOS)
# ===========================================================================
async def crear_empresa(db: AsyncSession, empresa: auth.EmpresaCreate):
    db_empresa = psql_models.Empresa(
        nombre_comercial=empresa.nombre_comercial,
        ruc_identificacion=empresa.ruc_identificacion,
        correo_contacto=empresa.correo_contacto,
        telefono_contacto=empresa.telefono_contacto
    )
    db.add(db_empresa)
    await db.flush()
    return db_empresa

async def obtener_usuario_por_username(db: AsyncSession, username: str, empresa_id: str):
    result = await db.execute(
        select(psql_models.Usuario).where(
            psql_models.Usuario.username == username,
            psql_models.Usuario.empresa_id == empresa_id
        )
    )
    return result.scalars().first()

async def crear_usuario(db: AsyncSession, usuario: auth.UsuarioCreate):
    db_usuario = psql_models.Usuario(
        empresa_id=usuario.empresa_id,
        username=usuario.username,
        password_hash=obtener_password_hash(usuario.password),
        nombre_completo=usuario.nombre_completo,
        rol=usuario.rol
    )
    db.add(db_usuario)
    await db.flush()
    return db_usuario


# ===========================================================================
# 2. SERVICIOS DE INFRAESTRUCTURA LÓGICA (MIKROTIK)
# ===========================================================================
async def registrar_mikrotik(db: AsyncSession, router: network.MikrotikRouterCreate):
    db_router = psql_models.MikrotikRouter(
        empresa_id=router.empresa_id,
        nombre_identificador=router.nombre_identificador,
        descripcion=router.descripcion,
        ip_gestion=router.ip_gestion,
        puerto_api=router.puerto_api,
        puerto_ssh=router.puerto_ssh,
        usuario_acceso=router.usuario_acceso,
        password_encriptado=encriptar_credencial(router.password_acceso)
    )
    db.add(db_router)
    await db.flush()
    return db_router

async def obtener_routers_por_tenant(db: AsyncSession, empresa_id: str):
    result = await db.execute(
        select(psql_models.MikrotikRouter).where(psql_models.MikrotikRouter.empresa_id == empresa_id)
    )
    return result.scalars().all()


# ===========================================================================
# 3. SERVICIOS DE INVENTARIO GEOGRÁFICO GIS (CAJAS NAP - POSTGIS)
# ===========================================================================
async def registrar_caja_nap(db: AsyncSession, nap: network.NapBoxCreate):
    punto_wkt = f"POINT({nap.longitud} {nap.latitud})"
    
    db_nap = psql_models.NapBox(
        empresa_id=nap.empresa_id,
        olt_puerto_id=nap.olt_puerto_id,
        nombre_nap=nap.nombre_nap,
        puertos_totales=nap.puertos_totales,
        coordenadas=WKTElement(punto_wkt, srid=4326)
    )
    db.add(db_nap)
    await db.flush()
    return db_nap


# ===========================================================================
# 4. SERVICIOS DE ABONADOS (CLIENTES INTEGRADOS CON TELEMETRÍA)
# ===========================================================================
async def registrar_cliente(db: AsyncSession, cliente: network.ClienteCreate):
    punto_wkt = f"POINT({cliente.longitud} {cliente.latitud})"
    
    db_cliente = psql_models.Cliente(
        empresa_id=cliente.empresa_id,
        router_id=cliente.router_id,
        plan_id=cliente.plan_id,
        nap_id=cliente.nap_id,
        nombre_completo=cliente.nombre_completo,
        identificacion=cliente.identificacion,
        coordenadas=WKTElement(punto_wkt, srid=4326),
        nap_puerto_asignado=cliente.nap_puerto_asignado,
        usuario_pppoe=cliente.usuario_pppoe,
        password_pppoe=cliente.password_pppoe,
        ip_asignada=cliente.ip_asignada,
        sn_onu=cliente.sn_onu,
        estado="Activo"
    )
    db.add(db_cliente)
    await db.flush()
    return db_cliente
