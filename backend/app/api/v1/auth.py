from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services import crud
from app.schemas import auth as auth_schema
from app.core.security import verificar_password, crear_token_acceso

router = APIRouter()

@router.post("/register", response_model=auth_schema.UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registrar_nuevo_usuario(usuario: auth_schema.UsuarioCreate, db: AsyncSession = Depends(get_db)):
    """
    Registra un usuario dentro de un Tenant (Empresa) específico verificando duplicados.
    """
    usuario_existente = await crud.obtener_usuario_por_username(
        db=db, username=usuario.username, empresa_id=usuario.empresa_id
    )
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado en esta empresa."
        )
    
    nuevo_usuario = await crud.crear_usuario(db=db, usuario=usuario)
    await db.commit()
    await db.refresh(nuevo_usuario)
    return nuevo_usuario

@router.post("/login")
async def iniciar_sesion(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    empresa_id: str = None, 
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de Login compatible con OAuth2. 
    Requiere el 'empresa_id' en los parámetros o cabecera para validar el aislamiento multi-tenant.
    """
    if not empresa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta el parámetro 'empresa_id' para validar el Tenant."
        )

    usuario = await crud.obtener_usuario_por_username(db=db, username=form_data.username, empresa_id=empresa_id)
    if not usuario or not verificar_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o usuario no pertenece a la empresa indicada.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar el token inyectando la identidad, la empresa y su rol de red
    jwt_token = crear_token_acceso(subject=usuario.username, empresa_id=usuario.empresa_id, rol=usuario.rol)
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "rol": usuario.rol,
        "empresa_id": usuario.empresa_id
    }
