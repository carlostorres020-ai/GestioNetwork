import uuid
from sqlalchemy import Table, Column, String, Integer, Boolean, ForeignKey, DateTime, Numeric, BigInteger, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.database.session import Base

# ===========================================================================
# 1. MODELO: EMPRESA (TENANT PRINCIPAL)
# ===========================================================================
class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_comercial = Column(String(150), nullable=False)
    ruc_identificacion = Column(String(20), nullable=False, unique=True)
    correo_contacto = Column(String(100), nullable=False)
    telefono_contacto = Column(String(20), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    routers = relationship("MikrotikRouter", back_populates="empresa", cascade="all, delete-orphan")
    planes = relationship("InternetPlan", back_populates="empresa", cascade="all, delete-orphan")
    olts = relationship("OltDevice", back_populates="empresa", cascade="all, delete-orphan")
    naps = relationship("NapBox", back_populates="empresa", cascade="all, delete-orphan")
    clientes = relationship("Cliente", back_populates="empresa", cascade="all, delete-orphan")


# ===========================================================================
# 2. MODELO: USUARIO (CONTROL DE ACCESO Y SEGURIDAD)
# ===========================================================================
class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("empresa_id", "username", name="unq_usuario_empresa"),
        CheckConstraint("rol IN ('administrador', 'soporte_noc', 'tecnico_campo')", name="chk_rol_usuario"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    rol = Column(String(30), nullable=False)
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    bloqueado_hasta = Column(DateTime(timezone=True), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="usuarios")


# ===========================================================================
# 3. MODELO: MIKROTIK_ROUTER (SALUD Y LOGÍSTICA DE RED)
# ===========================================================================
class MikrotikRouter(Base):
    __tablename__ = "mikrotik_routers"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre_identificador", name="unq_router_empresa"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nombre_identificador = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    ip_gestion = Column(String(45), nullable=False)
    puerto_api = Column(Integer, default=8728, nullable=False)
    puerto_ssh = Column(Integer, default=22, nullable=False)
    usuario_acceso = Column(String(100), nullable=False)
    password_encriptado = Column(Text, nullable=False)
    
    # Telemetría en tiempo real del equipo
    online = Column(Boolean, default=False, nullable=False)
    ultima_verificacion = Column(DateTime(timezone=True), nullable=True)
    cpu_uso_porcentaje = Column(Integer, default=0)
    memoria_libre_bytes = Column(BigInteger, default=0)
    memoria_total_bytes = Column(BigInteger, default=0)
    uptime_segundos = Column(BigInteger, default=0)
    fecha_hora_equipo = Column(DateTime(timezone=True), nullable=True)
    version_routeros = Column(String(30), nullable=True)
    modelo_hardware = Column(String(50), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="routers")
    clientes = relationship("Cliente", back_populates="router")


# ===========================================================================
# 4. MODELO: INTERNET_PLAN (INGENIERÍA DE TRÁFICO)
# ===========================================================================
class InternetPlan(Base):
    __tablename__ = "internet_plans"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre_plan", name="unq_plan_empresa"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nombre_plan = Column(String(100), nullable=False)
    velocidad_bajada = Column(String(20), nullable=False)
    velocidad_subida = Column(String(20), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    id_plan_subida_olt = Column(String(100), nullable=True)
    id_plan_bajada_olt = Column(String(100), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="planes")
    clientes = relationship("Cliente", back_populates="plan")


# ===========================================================================
# 5. MODELO: OLT_DEVICE (CABECERAS ÓPTICAS)
# ===========================================================================
class OltDevice(Base):
    __tablename__ = "olt_devices"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre_olt", name="unq_olt_empresa"),
        CheckConstraint("marca IN ('ZTE', 'Huawei')", name="chk_marca_olt"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nombre_olt = Column(String(100), nullable=False)
    marca = Column(String(30), nullable=False)
    modelo = Column(String(50), nullable=True)
    ip_gestion = Column(String(45), nullable=False)
    puerto_ssh = Column(Integer, default=22, nullable=False)
    usuario_acceso = Column(String(100), nullable=False)
    password_encriptado = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="olts")
    puertos = relationship("OltSlotPort", back_populates="olt", cascade="all, delete-orphan")


# ===========================================================================
# 6. MODELO: OLT_SLOT_PORT (ESTRUCTURA DE PUERTOS PON)
# ===========================================================================
class OltSlotPort(Base):
    __tablename__ = "olt_slots_ports"
    __table_args__ = (
        UniqueConstraint("olt_id", "nro_slot", "nro_puerto", name="unq_slot_puerto_olt"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    olt_id = Column(UUID(as_uuid=True), ForeignKey("olt_devices.id", ondelete="CASCADE"), nullable=False)
    nro_slot = Column(Integer, nullable=False)
    nro_puerto = Column(Integer, nullable=False)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    olt = relationship("OltDevice", back_populates="puertos")
    naps = relationship("NapBox", back_populates="puerto_pon")


# ===========================================================================
# 7. MODELO: NAP_BOX (INVENTARIO GEOGRÁFICO GIS)
# ===========================================================================
class NapBox(Base):
    __tablename__ = "nap_boxes"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre_nap", name="unq_nap_empresa"),
        CheckConstraint("puertos_totales IN (4, 8, 16, 32)", name="chk_puertos_totales_nap"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    olt_puerto_id = Column(UUID(as_uuid=True), ForeignKey("olt_slots_ports.id", ondelete="RESTRICT"), nullable=False)
    nombre_nap = Column(String(100), nullable=False)
    puertos_totales = Column(Integer, nullable=False)
    
    # Campo Geoespacial de PostGIS (Manejo de Mapas)
    coordenadas = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="naps")
    puerto_pon = relationship("OltSlotPort", back_populates="naps")
    clientes = relationship("Cliente", back_populates="nap")


# ===========================================================================
# 8. MODELO: CLIENTE (EL NÚCLEO CENTRAL CON TELEMETRÍA EXTENDIDA CAPA 1)
# ===========================================================================
class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("empresa_id", "usuario_pppoe", name="unq_pppoe_empresa"),
        UniqueConstraint("empresa_id", "ip_asignada", name="unq_ip_empresa"),
        CheckConstraint("estado IN ('Activo', 'Suspendido', 'Retirado')", name="chk_estado_cliente"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    router_id = Column(UUID(as_uuid=True), ForeignKey("mikrotik_routers.id", ondelete="RESTRICT"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("internet_plans.id", ondelete="RESTRICT"), nullable=False)
    nap_id = Column(UUID(as_uuid=True), ForeignKey("nap_boxes.id", ondelete="RESTRICT"), nullable=False)

    # Datos Abonado
    nombre_completo = Column(String(200), nullable=False)
    identificacion = Column(String(20), nullable=True)
    descripcion = Column(Text, nullable=True)
    coordenadas = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    nap_puerto_asignado = Column(Integer, nullable=False)

    # Red y Estado
    usuario_pppoe = Column(String(100), nullable=False)
    password_pppoe = Column(String(100), nullable=False)
    ip_asignada = Column(String(45), nullable=False)
    estado = Column(String(30), default="Activo", nullable=False)

    # Identificación Física Fibra Optica
    sn_onu = Column(String(50), unique=True, nullable=True)
    onu_id_interno = Column(Integer, nullable=True)

    # Bloque de parámetros de Telemetría Óptica (16 Parámetros Clave)
    olt_rx_power = Column(Numeric(5, 2), nullable=True)
    olt_tx_power = Column(Numeric(5, 2), nullable=True)
    ont_rx_power = Column(Numeric(5, 2), nullable=True)
    ont_tx_power = Column(Numeric(5, 2), nullable=True)
    distancia_fo_metros = Column(Integer, nullable=True)

    # Salud Física del Transceiver
    ont_temperatura = Column(Numeric(5, 2), nullable=True)
    ont_vcc = Column(Numeric(4, 2), nullable=True)
    ont_bias_corriente = Column(Numeric(6, 2), nullable=True)

    # Diagnóstico e historial
    motivo_ultima_desconexion = Column(Text, nullable=True)
    ultima_sincronizacion_telemetria = Column(DateTime(timezone=True), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="clientes")
    router = relationship("MikrotikRouter", back_populates="clientes")
    plan = relationship("InternetPlan", back_populates="clientes")
    nap = relationship("NapBox", back_populates="clientes")
