from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

# ===========================================================================
# ESQUEMAS PARA LA MAESTRA: EMPRESA (TENANT)
# ===========================================================================
class EmpresaBase(BaseModel):
    nombre_comercial: str = Field(..., max_length=150, description="Nombre de la empresa o ISP")
    ruc_identificacion: str = Field(..., max_length=20, description="RUC o Identificación fiscal única")
    correo_contacto: EmailStr = Field(..., description="Correo oficial de contacto")
    telefono_contacto: Optional[str] = Field(None, max_length=20)

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaResponse(EmpresaBase):
    id: UUID
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ===========================================================================
# ESQUEMAS PARA CONTROL DE ACCESO: USUARIOS
# ===========================================================================
class UsuarioBase(BaseModel):
    username: str = Field(..., min_length=4, max_length=50, description="Nombre de usuario para el login")
    nombre_completo: str = Field(..., max_length=150, description="Nombre y apellido del operador")
    rol: str = Field(..., description="Roles válidos: administrador, soporte_noc, tecnico_campo")

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8, description="Contraseña de acceso (mínimo 8 caracteres)")
    empresa_id: UUID = Field(..., description="ID del Tenant al que pertenece")

class UsuarioResponse(UsuarioBase):
    id: UUID
    empresa_id: UUID
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ===========================================================================
# ESQUEMAS PARA AUTENTICACIÓN (LOGIN) Y TOKENS JWT
# ===========================================================================
class LoginRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario del operador")
    password: str = Field(..., description="Contraseña en texto plano")
    empresa_id: UUID = Field(..., description="ID de la empresa/Tenant para validación")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre_completo: str
