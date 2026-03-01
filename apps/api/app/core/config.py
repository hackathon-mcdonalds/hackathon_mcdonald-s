"""
Configuración central de la aplicación.

Pydantic-settings lee automáticamente las variables de entorno.
Incluye validaciones estrictas por entorno para prevenir
configuraciones inseguras en staging/producción.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import Literal
import json


class Settings(BaseSettings):
    # ── Aplicación ────────────────────────────────────────────────
    app_name: str = "CibusChain API"
    app_version: str = "0.1.0"

    # ── Base de Datos ────────────────────────────────────────────
    database_url: str

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Seguridad ────────────────────────────────────────────────
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # ── Entorno ──────────────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "info"

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8081"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Permite pasar los orígenes como JSON string desde docker-compose."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    # ── Google Maps (para ETA de voluntarios) ────────────────────
    google_maps_api_key: str = ""

    # ── Sentinel ─────────────────────────────────────────────────
    sentinel_pis_threshold: float = 0.85
    sentinel_check_interval_seconds: int = 60

    # ── Validaciones estrictas por entorno ────────────────────────

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "database_url debe usar el driver asyncpg: "
                "postgresql+asyncpg://user:pass@host:port/dbname"
            )
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Falla al arrancar si la configuración de producción es insegura."""
        if self.environment in ("staging", "production"):
            if len(self.secret_key) < 32:
                raise ValueError(
                    f"secret_key debe tener al menos 32 caracteres en {self.environment}. "
                    "Genera una con: openssl rand -hex 32"
                )
            if not self.google_maps_api_key:
                raise ValueError(
                    f"google_maps_api_key es requerida en {self.environment}"
                )
        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Instancia global
settings = Settings()
