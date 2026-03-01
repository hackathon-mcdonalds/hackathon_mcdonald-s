"""
CibusChain API — Punto de entrada principal

Configura la aplicación, conecta los routers, y define comportamientos globales.
No contiene lógica de negocio.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, dispose_db, AsyncSessionLocal
from app.core.logging import setup_logging, get_logger
from app.routers import branches, missions, volunteers, receivers, sentinel, fiscal

logger = get_logger(__name__)


# ── Lifecycle ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranque
    setup_logging(settings.log_level)
    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name, settings.app_version, settings.environment,
    )
    await init_db()
    yield
    # Apagado
    logger.info("Shutting down...")
    await dispose_db()


# ── Aplicación ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="""\
    Infraestructura tecnológica para el rescate de alimentos preparados.
    
    ## Componentes
    - **Sentinel**: predicción de excedentes mediante ML
    - **Missions**: gestión del ciclo de vida de misiones de rescate  
    - **FiscalFlow**: liquidación fiscal automática (Art. 27 LISR)
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)


# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(branches.router,    prefix="/api/v1/branches",    tags=["Sucursales"])
app.include_router(missions.router,    prefix="/api/v1/missions",    tags=["Misiones"])
app.include_router(volunteers.router,  prefix="/api/v1/volunteers",  tags=["Voluntarios"])
app.include_router(receivers.router,   prefix="/api/v1/receivers",   tags=["Receptores"])
app.include_router(sentinel.router,    prefix="/api/v1/sentinel",    tags=["Sentinel"])
app.include_router(fiscal.router,      prefix="/api/v1/fiscal",      tags=["FiscalFlow"])


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
async def health_check():
    """
    Verifica que la API, la base de datos y Redis estén respondiendo.
    Docker, Railway y balanceadores de carga usan este endpoint.
    """
    from sqlalchemy import text
    from fastapi.responses import JSONResponse
    import redis.asyncio as aioredis

    health = {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "database": "ok",
        "redis": "ok",
    }

    # Check DB
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        health["status"] = "degraded"
        health["database"] = f"error: {type(e).__name__}"
        logger.warning("Health check: database unreachable — %s", e)

    # Check Redis
    try:
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
    except Exception as e:
        health["status"] = "degraded"
        health["redis"] = f"error: {type(e).__name__}"
        logger.warning("Health check: Redis unreachable — %s", e)

    status_code = 200 if health["status"] == "ok" else 503
    return JSONResponse(content=health, status_code=status_code)


@app.get("/", tags=["Sistema"])
async def root():
    return {
        "message": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }
