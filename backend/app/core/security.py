from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Any
import jwt
import uuid

SECRET_KEY = 'TU_CLAVE_SECRETA_MUY_LARGA_Y_SEGURA'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def obtener_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def crear_token_acceso(subject: str, empresa_id: Any, rol: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # Aseguramos que el UUID sea convertido a string para el JSON del JWT
    empresa_id_str = str(empresa_id) if isinstance(empresa_id, uuid.UUID) else empresa_id
    
    to_encode = {'sub': subject, 'empresa_id': empresa_id_str, 'rol': rol, 'exp': expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
