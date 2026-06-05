from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database.session import get_db
from app.schemas import network
from app.services import crud

router = APIRouter()

# ===========================================================================
# ENDPOINTS: MIKROTIK ROUTERS
# ===========================================================================
@router.post("/routers", response_model=network.MikrotikRouterResponse, status_code=status.HTTP_201_CREATED, tags=["MikroTik"])
async def registrar_router_mikrotik(router_in: network.MikrotikRouterCreate, db: AsyncSession = Depends(get_db)):
    """
    Registra un nuevo router MikroTik en el sistema y cifra de forma segura sus credenciales.
    """
    try:
        nuevo_router = await crud.registrar_mikrotik(db=db, router=router_in)
        return nuevo_router
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar el router MikroTik. Verifique que el identificador sea único: {str(e)}"
        )

@router.get("/routers/tenant/{empresa_id}", response_model=List[network.MikrotikRouterResponse], tags=["MikroTik"])
async def listar_routers_por_empresa(empresa_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Retorna la lista de routers MikroTik asociados a un Tenant (Empresa) específico.
    """
    routers = await crud.obtener_routers_por_tenant(db=db, empresa_id=str(empresa_id))
    return routers


# ===========================================================================
# ENDPOINTS: GEOLOCALIZACIÓN GIS (CAJAS NAP)
# ===========================================================================
@router.post("/naps", response_model=network.NapBoxResponse, status_code=status.HTTP_201_CREATED, tags=["GIS & Inventario"])
async def registrar_caja_nap_gis(nap_in: network.NapBoxCreate, db: AsyncSession = Depends(get_db)):
    """
    Da de alta una caja NAP en el inventario, transformando las coordenadas a geometría espacial PostGIS.
    """
    try:
        nueva_nap = await crud.registrar_caja_nap(db=db, nap=nap_in)
        
        # Formatear la respuesta manual debido al objeto binario WKTElement de GeoAlchemy
        return network.NapBoxResponse(
            id=nueva_nap.id,
            empresa_id=nueva_nap.empresa_id,
            olt_puerto_id=nueva_nap.olt_puerto_id,
            nombre_nap=nueva_nap.nombre_nap,
            puertos_totales=nueva_nap.puertos_totales,
            latitud=nap_in.latitud,
            longitud=nap_in.longitud
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar la caja NAP. Verifique la coherencia de datos: {str(e)}"
        )


# ===========================================================================
# ENDPOINTS: ABONADOS Y CLIENTES
# ===========================================================================
@router.post("/clientes", response_model=network.ClienteResponse, status_code=status.HTTP_201_CREATED, tags=["Clientes & Telemetría"])
async def registrar_nuevo_cliente(cliente_in: network.ClienteCreate, db: AsyncSession = Depends(get_db)):
    """
    Inserta un abonado vinculando su plan, router de acceso, caja NAP y coordenadas espaciales.
    """
    try:
        nuevo_cliente = await crud.registrar_cliente(db=db, cliente=cliente_in)
        return nuevo_cliente
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar el cliente. Verifique duplicados en IP o Usuario PPPoE: {str(e)}"
        )
