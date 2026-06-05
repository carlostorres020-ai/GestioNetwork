from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import ALGORITHM
from app.database.session import get_db
from app.services import crud
from pydantic import BaseModel
from uuid import UUID

# Configura la ruta de donde FastAPI extraerá automáticamente el Header 'Authorization: Bearer <TOKEN>'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class TokenData(BaseModel):
    username: str or None = None
    empresa_id: UUID or None = None
    rol: str or None = None

async def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    """
    Interceptor global que decodifica el JWT, valida la firma, extrae el Tenant (empresa_id) 
    y confirma que el usuario exista y esté activo en la base de datos.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de acceso.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        empresa_id_str: str = payload.get("empresa_id")
        rol: str = payload.get("rol")
        
        if username is None or empresa_id_str is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, empresa_id=UUID(empresa_id_str), rol=rol)
    except JWTError:
        raise credentials_exception

    # Buscar el usuario asegurando el aislamiento estricto por Tenant
    usuario = await crud.obtener_usuario_por_username(
        db=db, username=token_data.username, empresa_id=str(token_data.empresa_id)
    )
    if usuario is None:
        raise credentials_exception
        
    return usuario

class ControlRoles:
    """
    Permite restringir endpoints específicos según los roles del personal del ISP.
    Uso: Depends(ControlRoles(["administrador", "soporte_noc"]))
    """
    def __init__(self, roles_permitidos: list[str]):
        self.roles_permitidos = roles_permitidos

    def __call__(self, usuario_actual=Depends(obtener_usuario_actual)):
        if usuario_actual.rol not in self.roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_03_FORBIDDEN,
                detail="Acceso denegado: No tienes los privilegios necesarios para realizar esta acción."
            )
        return usuario_actual
