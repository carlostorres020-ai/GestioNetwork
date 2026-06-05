import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.network import router as network_router
from app.api.v1.auth import router as auth_router

ENV = os.getenv("ENV", "production").lower()

docs_url = None if ENV == "production" else "/docs"
redoc_url = None if ENV == "production" else "/redoc"

app = FastAPI(
    title="GestioNetwork API",
    description="Ecosistema seguro de gestión y telemetría de red (NOC + GIS) - Multi-Tenant",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url
)

allowed_origins = ["*"] if ENV != "production" else ["https://gpon.monitoreoct.com", "https://mkt.monitoreoct.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inyección de módulos de rutas v1
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticación & Tenants"])
app.include_router(network_router, prefix="/api/v1", tags=["Infraestructura de Red"])

@app.get("/", tags=["Validación"])
async def estado_servidor():
    return {
        "sistema": "GestioNetwork",
        "estado": "Operacional",
        "entorno": ENV,
        "seguridad": "Filtros Activos" if ENV == "production" else "Modo Desarrollo"
    }
