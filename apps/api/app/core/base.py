"""
Base declarativa de SQLAlchemy.

Aislada en su propio módulo para evitar dependencias circulares
entre database.py y los modelos.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos ORM."""
    pass
