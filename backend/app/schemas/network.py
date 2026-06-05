from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# ===========================================================================
# 1. ESQUEMAS: MIKROTIK ROUTERS
# ===========================================================================
class MikrotikRouterBase(BaseModel):
    nombre_identificador: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    ip_gestion: str = Field(..., description="IP o dominio del equipo")
    puerto_api: int = Field(8728)
    puerto_ssh: int = Field(22)
    usuario_acceso: str = Field(..., max_length=100)

class MikrotikRouterCreate(MikrotikRouterBase):
    password_acceso: str = Field(..., description="Contraseña en texto plano para encriptar")
    empresa_id: UUID

class MikrotikRouterResponse(MikrotikRouterBase):
    id: UUID
    empresa_id: UUID
    online: bool
    ultima_verificacion: Optional[datetime] = None
    cpu_uso_porcentaje: int
    memoria_libre_bytes: int
    memoria_total_bytes: int
    uptime_segundos: int
    version_routeros: Optional[str] = None
    modelo_hardware: Optional[str] = None

    class Config:
        from_attributes = True


# ===========================================================================
# 2. ESQUEMAS: OLT DEVICES Y PUERTOS PON
# ===========================================================================
class OltDeviceCreate(BaseModel):
    nombre_olt: str = Field(..., max_length=100)
    marca: str = Field(..., description="ZTE o Huawei")
    modelo: Optional[str] = Field(None, max_length=50)
    ip_gestion: str
    puerto_ssh: int = 22
    usuario_acceso: str
    password_acceso: str
    empresa_id: UUID

    @field_validator('marca')
    @classmethod
    def validar_marca(cls, v: str) -> str:
        if v not in ('ZTE', 'Huawei'):
            raise ValueError('La marca de la OLT debe ser ZTE o Huawei')
        return v

class OltDeviceResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre_olt: str
    marca: str
    modelo: Optional[str]
    ip_gestion: str
    puerto_ssh: int

    class Config:
        from_attributes = True


# ===========================================================================
# 3. ESQUEMAS: CAJAS NAP (INVENTARIO GEOGRÁFICO)
# ===========================================================================
class NapBoxCreate(BaseModel):
    olt_puerto_id: UUID
    nombre_nap: str = Field(..., max_length=100)
    puertos_totales: int = Field(..., description="4, 8, 16 o 32")
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    empresa_id: UUID

    @field_validator('puertos_totales')
    @classmethod
    def validar_puertos(cls, v: int) -> int:
        if v not in (4, 8, 16, 32):
            raise ValueError('Los puertos totales de una NAP deben ser 4, 8, 16 o 32')
        return v

class NapBoxResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    olt_puerto_id: UUID
    nombre_nap: str
    puertos_totales: int
    latitud: float
    longitud: float

    class Config:
        from_attributes = True


# ===========================================================================
# 4. ESQUEMAS: CLIENTES (INTEGRACIÓN PPPoE + GPON + TELEMETRÍA 16 PARÁMETROS)
# ===========================================================================
class ClienteCreate(BaseModel):
    empresa_id: UUID
    router_id: UUID
    plan_id: UUID
    nap_id: UUID
    nombre_completo: str = Field(..., max_length=200)
    identificacion: Optional[str] = Field(None, max_length=20)
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    nap_puerto_asignado: int
    usuario_pppoe: str = Field(..., max_length=100)
    password_pppoe: str = Field(..., max_length=100)
    ip_asignada: str
    sn_onu: Optional[str] = Field(None, max_length=50, description="Serial físico de la ONT")

class ClienteResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre_completo: str
    usuario_pppoe: str
    ip_asignada: str
    estado: str
    sn_onu: Optional[str] = None
    onu_id_interno: Optional[int] = None
    
    # Bloque de Potencias y Distancia
    olt_rx_power: Optional[float] = None
    olt_tx_power: Optional[float] = None
    ont_rx_power: Optional[float] = None
    ont_tx_power: Optional[float] = None
    distancia_fo_metros: Optional[int] = None
    
    # Diagnóstico Eléctrico/Térmico
    ont_temperatura: Optional[float] = None
    ont_vcc: Optional[float] = None
    ont_bias_corriente: Optional[float] = None
    
    ultima_sincronizacion_telemetria: Optional[datetime] = None

    class Config:
        from_attributes = True
