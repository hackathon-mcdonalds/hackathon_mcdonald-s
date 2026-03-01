"""
Conexión a la base de datos — async, hardened.

Pool configurado con pre-ping (detecta conexiones muertas) y recycle
(previene timeouts de PostgreSQL). El generador get_db() NO hace
auto-commit: el caller controla las transacciones.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Motor con pool hardened
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,           # detecta conexiones muertas antes de usarlas
    pool_recycle=3600,            # recicla conexiones cada 1h (evita timeout de PG)
    echo=settings.environment == "development",
)

# Fábrica de sesiones
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Verifica conectividad con la base de datos al arrancar."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda conn: None)
        logger.info("Database connection established")
    except Exception:
        logger.exception("Failed to connect to database")
        raise


async def dispose_db() -> None:
    """Cierra el pool de conexiones al apagar la aplicación."""
    await engine.dispose()
    logger.info("Database connection pool closed")


async def get_db():
    """
    Generador de sesiones para FastAPI Depends().

    NO hace auto-commit — los endpoints que escriben deben llamar
    session.commit() explícitamente. Rollback automático en caso de error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
