-- ===========================================================================
-- FASE 1: SCRIPT DE MIGRACIÓN COMPLETO - INFRAESTRUCTURA DE BASE DE DATOS
-- PROYECTO: SISTEMA DE GESTIÓN E INTELIGENCIA DE RED (GESTIONETWORK) MULTI-TENANT
-- SEGURIDAD: DISEÑADO PARA VPS PÚBLICA CON ACCESO RESTRINGIDO
-- ===========================================================================

-- Habilitar la extensión PostGIS para el manejo de mapas y geometría espacial
CREATE EXTENSION IF NOT EXISTS postgis;

-- Habilitar la extensión para generación de UUIDs nativos
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================================================
-- TABLA MAESTRA: EMPRESAS (TENANTS)
-- Base del aislamiento Multi-Tenant. Todo recurso pertenece a una empresa.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS empresas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_comercial VARCHAR(150) NOT NULL,
    ruc_identificacion VARCHAR(20) NOT NULL UNIQUE,
    correo_contacto VARCHAR(100) NOT NULL,
    telefono_contacto VARCHAR(20),
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE empresas IS 'Tabla maestra para el aislamiento de datos multi-tenant.';

-- ===========================================================================
-- TABLA 1: USUARIOS (CONTROL DE ACCESO, ROLES Y CAPTCHA)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    rol VARCHAR(30) NOT NULL CHECK (rol IN ('administrador', 'soporte_noc', 'tecnico_campo')),
    intentos_fallidos INT DEFAULT 0 NOT NULL,
    bloqueado_hasta TIMESTAMP WITH TIME ZONE,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unq_usuario_empresa UNIQUE (empresa_id, username)
);

COMMENT ON TABLE usuarios IS 'Usuarios del sistema con autenticación protegida bajo modelo multi-tenant.';

-- ===========================================================================
-- TABLA 2: MIKROTIK_ROUTERS (NODOS LÓGICOS Y DESCUBRIMIENTO DE HARDWARE)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS mikrotik_routers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    nombre_identificador VARCHAR(100) NOT NULL,
    descripcion TEXT,
    
    -- Parámetros de Conexión Personalizados
    ip_gestion VARCHAR(45) NOT NULL,
    puerto_api INT NOT NULL DEFAULT 8728,
    puerto_ssh INT NOT NULL DEFAULT 22,
    usuario_acceso VARCHAR(100) NOT NULL,
    password_encriptado TEXT NOT NULL, -- Guardado con cifrado simétrico AES-256
    
    -- Estado de Conectividad en Tiempo Real
    online BOOLEAN DEFAULT FALSE NOT NULL,
    ultima_verificacion TIMESTAMP WITH TIME ZONE,
    
    -- Variables de Descubrimiento de Hardware (Métricas de Salud)
    cpu_uso_porcentaje INT DEFAULT 0,
    memoria_libre_bytes BIGINT DEFAULT 0,
    memoria_total_bytes BIGINT DEFAULT 0,
    uptime_segundos BIGINT DEFAULT 0,
    fecha_hora_equipo TIMESTAMP WITH TIME ZONE,
    version_routeros VARCHAR(30),
    modelo_hardware VARCHAR(50),
    
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unq_router_empresa UNIQUE (empresa_id, nombre_identificador)
);

COMMENT ON TABLE mikrotik_routers IS 'Nodos lógicos MikroTik con puertos customizados y métricas de rendimiento extraídas por API/SSH.';

-- ===========================================================================
-- TABLA 3: INTERNET_PLANS (PLANES DE VELOCIDAD E INGENIERÍA DE TRÁFICO)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS internet_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    nombre_plan VARCHAR(100) NOT NULL,
    velocidad_bajada VARCHAR(20) NOT NULL,
    velocidad_subida VARCHAR(20) NOT NULL,
    precio NUMERIC(10, 2) NOT NULL,
    
    -- Mapeo estricto para perfiles de tráfico OLT (Traffic DBA)
    id_plan_subida_olt VARCHAR(100),
    id_plan_bajada_olt VARCHAR(100),
    
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unq_plan_empresa UNIQUE (empresa_id, nombre_plan)
);

COMMENT ON TABLE internet_plans IS 'Planes de velocidad comerciales vinculados a las reglas de colas y perfiles OLT.';

-- ===========================================================================
-- TABLA 4: OLT_DEVICES (CABECERAS ÓPTICAS DE DISTRIBUCIÓN)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS olt_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    nombre_olt VARCHAR(100) NOT NULL,
    marca VARCHAR(30) NOT NULL CHECK (marca IN ('ZTE', 'Huawei')),
    modelo VARCHAR(50),
    ip_gestion VARCHAR(45) NOT NULL,
    puerto_ssh INT NOT NULL DEFAULT 22,
    usuario_acceso VARCHAR(100) NOT NULL,
    password_encriptado TEXT NOT NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unq_olt_empresa UNIQUE (empresa_id, nombre_olt)
);

COMMENT ON TABLE olt_devices IS 'Equipos OLT asociados a cada Tenant para el aprovisionamiento físico GPON.';

-- ===========================================================================
-- TABLA 5: OLT_SLOTS_PORTS (ARQUITECTURA DE PUERTOS PON)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS olt_slots_ports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    olt_id UUID NOT NULL REFERENCES olt_devices(id) ON DELETE CASCADE,
    nro_slot INT NOT NULL,
    nro_puerto INT NOT NULL,
    descripcion VARCHAR(255),
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unq_slot_puerto_olt UNIQUE (olt_id, nro_slot, nro_puerto)
);

COMMENT ON TABLE olt_slots_ports IS 'Mapeo físico de Slots y Puertos PON para colgar las cajas NAP.';

-- ===========================================================================
-- TABLA 6: NAP_BOXES (CAJAS DE DISTRIBUCIÓN FTTH / INVENTARIO GEOGRÁFICO)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS nap_boxes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    olt_puerto_id UUID NOT NULL REFERENCES olt_slots_ports(id) ON DELETE RESTRICT,
    nombre_nap VARCHAR(100) NOT NULL,
    puertos_totales INT NOT NULL CHECK (puertos_totales IN (4, 8, 16, 32)),
    
    -- Ubicación Geoespacial estricta para PostGIS (Longitud, Latitud, SRID 4326 WGS84)
    coordenadas GEOMETRY(Point, 4326) NOT NULL,
    
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT unq_nap_empresa UNIQUE (empresa_id, nombre_nap)
);

COMMENT ON TABLE nap_boxes IS 'Cajas divisorias (NAP) ubicadas geográficamente y mapeadas a un puerto PON específico.';

-- ===========================================================================
-- TABLA 7: CLIENTES (EL NÚCLEO CENTRAL DE INTEGRACIÓN Y TELEMETRÍA EXTENDIDA)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    router_id UUID NOT NULL REFERENCES mikrotik_routers(id) ON DELETE RESTRICT,
    plan_id UUID NOT NULL REFERENCES internet_plans(id) ON DELETE RESTRICT,
    nap_id UUID NOT NULL REFERENCES nap_boxes(id) ON DELETE RESTRICT,
    
    -- Datos del Abonado e Inventario
    nombre_completo VARCHAR(200) NOT NULL,
    identificacion VARCHAR(20),
    descripcion TEXT,
    coordenadas GEOMETRY(Point, 4326) NOT NULL,
    nap_puerto_asignado INT NOT NULL,
    
    -- Datos Lógicos de Red (MikroTik)
    usuario_pppoe VARCHAR(100) NOT NULL,
    password_pppoe VARCHAR(100) NOT NULL,
    ip_asignada VARCHAR(45) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Suspendido', 'Retirado')),
    
    -- Parámetros Físicos del Hardware Óptico (Atar Serial de ONT)
    sn_onu VARCHAR(50) UNIQUE,
    onu_id_interno INT,
    
    -- Bloque de Telemetría Extendida (Monitoreo Predictivo Capa 1)
    olt_rx_power NUMERIC(5,2),
    olt_tx_power NUMERIC(5,2),
    ont_rx_power NUMERIC(5,2),
    ont_tx_power NUMERIC(5,2),
    distancia_fo_metros INT,
    
    -- Diagnóstico de Salud Eléctrica y Física del Transceiver
    ont_temperatura NUMERIC(5,2),
    ont_vcc NUMERIC(4,2),
    ont_bias_corriente NUMERIC(6,2),
    
    -- Historial de Estabilidad de Enlace
    motivo_ultima_desconexion TEXT,
    ultima_sincronizacion_telemetria TIMESTAMP WITH TIME ZONE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unq_pppoe_empresa UNIQUE (empresa_id, usuario_pppoe),
    CONSTRAINT unq_ip_empresa UNIQUE (empresa_id, ip_asignada)
);

COMMENT ON TABLE clientes IS 'Núcleo del sistema. Une la lógica PPPoE, la física GPON, los Mapas GIS y almacena la telemetría del enlace.';

-- ===========================================================================
-- CREACIÓN DE ÍNDICES OPTIMIZADOS PARA RENDIMIENTO Y SEGURIDAD
-- ===========================================================================
CREATE INDEX IF NOT EXISTS idx_nap_boxes_coords ON nap_boxes USING GIST (coordenadas);
CREATE INDEX IF NOT EXISTS idx_clientes_coords ON clientes USING GIST (coordenadas);
CREATE INDEX IF NOT EXISTS idx_usuarios_tenant ON usuarios(empresa_id);
CREATE INDEX IF NOT EXISTS idx_routers_tenant ON mikrotik_routers(empresa_id);
CREATE INDEX IF NOT EXISTS idx_planes_tenant ON internet_plans(empresa_id);
CREATE INDEX IF NOT EXISTS idx_clientes_tenant ON clientes(empresa_id);
CREATE INDEX IF NOT EXISTS idx_clientes_sn ON clientes(sn_onu) WHERE sn_onu IS NOT NULL;

-- ===========================================================================
-- VISTAS INTELIGENTES AUTOMATIZADAS (CANTIDAD DE CLIENTES EN TIEMPO REAL)
-- ===========================================================================
CREATE OR REPLACE VIEW vista_resumen_planes AS
SELECT 
    p.empresa_id,
    p.id AS plan_id,
    p.nombre_plan,
    p.velocidad_bajada,
    p.velocidad_subida,
    p.precio,
    COUNT(c.id) AS total_clientes_asociados
FROM internet_plans p
LEFT JOIN clientes c ON p.id = c.plan_id AND c.estado = 'Activo'
GROUP BY p.empresa_id, p.id, p.nombre_plan, p.velocidad_bajada, p.velocidad_subida, p.precio;

CREATE OR REPLACE VIEW vista_ocupacion_naps AS
SELECT 
    n.empresa_id,
    n.id AS nap_id,
    n.nombre_nap,
    sp.nro_slot,
    sp.nro_puerto AS nro_puerto_pon,
    n.puertos_totales,
    COUNT(c.id) AS puertos_ocupados,
    (n.puertos_totales - COUNT(c.id)) AS puertos_disponibles
FROM nap_boxes n
JOIN olt_slots_ports sp ON n.olt_puerto_id = sp.id
LEFT JOIN clientes c ON n.id = c.nap_id AND c.estado != 'Retirado'
GROUP BY n.empresa_id, n.id, n.nombre_nap, sp.nro_slot, sp.nro_puerto, n.puertos_totales;
