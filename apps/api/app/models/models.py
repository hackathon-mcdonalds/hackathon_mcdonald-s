"""
Modelos de la base de datos.

Un modelo es la representación de una tabla en Python.
SQLAlchemy lee estos modelos y Alembic genera el SQL para crear las tablas.

IMPORTANTE: Si cambias un modelo, necesitas crear una migración con Alembic.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Boolean, Text, Numeric, DateTime,
    ForeignKey, Enum as SAEnum, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.core.base import Base
from app.models.base import TimestampMixin, RepresentableMixin


# ── Enums de Python (espejo de los enums de PostgreSQL) ──────────────────────
class MissionStatus(str, enum.Enum):
    pending   = "pending"
    assigned  = "assigned"
    picked_up = "picked_up"
    delivered = "delivered"
    expired   = "expired"
    cancelled = "cancelled"

class MissionType(str, enum.Enum):
    volunteer   = "volunteer"
    auto_pickup = "auto_pickup"

class ActorType(str, enum.Enum):
    volunteer      = "volunteer"
    receiver_staff = "receiver_staff"

class TransportMode(str, enum.Enum):
    walking = "walking"
    cycling = "cycling"
    scooter = "scooter"
    driving = "driving"

class ReportStatus(str, enum.Enum):
    draft     = "draft"
    submitted = "submitted"
    accepted  = "accepted"


# ── Tabla 1: Sucursales ───────────────────────────────────────────────────────
class Branch(TimestampMixin, RepresentableMixin, Base):
    __tablename__ = "branches"

    id                  : Mapped[uuid.UUID]         = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name                : Mapped[str]               = mapped_column(String(120), nullable=False)
    address             : Mapped[str]               = mapped_column(Text, nullable=False)
    city                : Mapped[str]               = mapped_column(String(80), nullable=False)
    state               : Mapped[str]               = mapped_column(String(80), nullable=False)
    latitude            : Mapped[float]             = mapped_column(Numeric(10, 7), nullable=False)
    longitude           : Mapped[float]             = mapped_column(Numeric(10, 7), nullable=False)
    pos_system          : Mapped[str]               = mapped_column(String(60), nullable=False, default="oracle_symphony")
    primary_receiver_id : Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("receivers.id"), nullable=True)
    active              : Mapped[bool]              = mapped_column(Boolean, nullable=False, default=True)

    # Relaciones
    primary_receiver : Mapped[Optional["Receiver"]]   = relationship("Receiver", foreign_keys=[primary_receiver_id])
    product_types    : Mapped[list["ProductType"]]     = relationship("ProductType", back_populates="branch")
    missions         : Mapped[list["Mission"]]         = relationship("Mission", back_populates="branch")
    fiscal_reports   : Mapped[list["FiscalReport"]]    = relationship("FiscalReport", back_populates="branch")


# ── Tabla 2: Catálogo de Productos ────────────────────────────────────────────
class ProductType(RepresentableMixin, Base):
    __tablename__ = "product_types"

    id                      : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id               : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    name                    : Mapped[str]        = mapped_column(String(120), nullable=False)
    sku                     : Mapped[Optional[str]] = mapped_column(String(40))
    weight_grams            : Mapped[float]      = mapped_column(Numeric(6, 1), nullable=False)
    commercial_ttl_minutes  : Mapped[int]        = mapped_column(Integer, nullable=False)
    safety_ttl_minutes      : Mapped[int]        = mapped_column(Integer, nullable=False)
    sentinel_trigger_pct    : Mapped[float]      = mapped_column(Numeric(3, 2), nullable=False, default=0.85)
    active                  : Mapped[bool]       = mapped_column(Boolean, nullable=False, default=True)
    created_at              : Mapped[datetime]   = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    branch : Mapped["Branch"] = relationship("Branch", back_populates="product_types")

    __table_args__ = (
        Index("idx_product_types_branch_id", "branch_id"),
    )


# ── Tabla 3: Eventos del POS ──────────────────────────────────────────────────
class PosEvent(RepresentableMixin, Base):
    __tablename__ = "pos_events"

    id              : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id       : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    product_type_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_types.id"), nullable=False)
    quantity        : Mapped[int]       = mapped_column(Integer, nullable=False)
    prepared_at     : Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at      : Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False)
    sold_quantity   : Mapped[int]       = mapped_column(Integer, nullable=False, default=0)
    created_at      : Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="pos_events_quantity_positive"),
        Index("idx_pos_events_branch_prepared", "branch_id", "prepared_at"),
    )


# ── Tabla 4: Predicciones de Sentinel ────────────────────────────────────────
class SentinelPrediction(RepresentableMixin, Base):
    __tablename__ = "sentinel_predictions"

    id                : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id         : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    product_type_id   : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_types.id"), nullable=False)
    pos_event_id      : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pos_events.id"), nullable=False)
    predicted_surplus : Mapped[int]       = mapped_column(Integer, nullable=False)
    pis_score         : Mapped[float]     = mapped_column(Numeric(4, 3), nullable=False)
    mission_created   : Mapped[bool]      = mapped_column(Boolean, nullable=False, default=False)
    created_at        : Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_sentinel_predictions_branch_id", "branch_id"),
    )


# ── Tabla 5: Receptores ───────────────────────────────────────────────────────
class Receiver(TimestampMixin, RepresentableMixin, Base):
    __tablename__ = "receivers"

    id             : Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name           : Mapped[str]            = mapped_column(String(150), nullable=False)
    legal_name     : Mapped[Optional[str]]  = mapped_column(String(200))
    rfc            : Mapped[Optional[str]]  = mapped_column(String(13))
    donataria_auth : Mapped[Optional[str]]  = mapped_column(String(60))
    address        : Mapped[str]            = mapped_column(Text, nullable=False)
    latitude       : Mapped[float]          = mapped_column(Numeric(10, 7), nullable=False)
    longitude      : Mapped[float]          = mapped_column(Numeric(10, 7), nullable=False)
    contact_name   : Mapped[Optional[str]]  = mapped_column(String(100))
    contact_phone  : Mapped[Optional[str]]  = mapped_column(String(20))
    active         : Mapped[bool]           = mapped_column(Boolean, nullable=False, default=True)

    # Relaciones
    missions : Mapped[list["Mission"]] = relationship("Mission", back_populates="receiver")


# ── Tabla 6: Voluntarios ──────────────────────────────────────────────────────
class Volunteer(TimestampMixin, RepresentableMixin, Base):
    __tablename__ = "volunteers"

    id                : Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name         : Mapped[str]            = mapped_column(String(150), nullable=False)
    phone             : Mapped[str]            = mapped_column(String(20), nullable=False, unique=True)
    email             : Mapped[Optional[str]]  = mapped_column(String(150), unique=True)
    transport_mode    : Mapped[TransportMode]  = mapped_column(SAEnum(TransportMode), nullable=False, default=TransportMode.walking)
    trust_points      : Mapped[int]            = mapped_column(Integer, nullable=False, default=0)
    university        : Mapped[Optional[str]]  = mapped_column(String(150))
    student_id        : Mapped[Optional[str]]  = mapped_column(String(60))
    active            : Mapped[bool]           = mapped_column(Boolean, nullable=False, default=True)
    last_location_lat : Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    last_location_lng : Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    last_seen_at      : Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relaciones
    missions         : Mapped[list["Mission"]]        = relationship("Mission", back_populates="volunteer")
    trust_points_log : Mapped[list["TrustPointsLog"]] = relationship("TrustPointsLog", back_populates="volunteer")


# ── Tabla 7: Misiones ─────────────────────────────────────────────────────────
class Mission(TimestampMixin, RepresentableMixin, Base):
    __tablename__ = "missions"

    id                      : Mapped[uuid.UUID]         = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id               : Mapped[uuid.UUID]         = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    product_type_id         : Mapped[uuid.UUID]         = mapped_column(UUID(as_uuid=True), ForeignKey("product_types.id"), nullable=False)
    sentinel_prediction_id  : Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("sentinel_predictions.id"))
    receiver_id             : Mapped[uuid.UUID]         = mapped_column(UUID(as_uuid=True), ForeignKey("receivers.id"), nullable=False)
    volunteer_id            : Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("volunteers.id"))
    mission_type            : Mapped[MissionType]       = mapped_column(SAEnum(MissionType), nullable=False)
    status                  : Mapped[MissionStatus]     = mapped_column(SAEnum(MissionStatus), nullable=False, default=MissionStatus.pending)
    quantity_units          : Mapped[int]               = mapped_column(Integer, nullable=False)
    weight_kg               : Mapped[float]             = mapped_column(Numeric(6, 2), nullable=False)
    expires_at              : Mapped[datetime]          = mapped_column(DateTime(timezone=True), nullable=False)
    assigned_at             : Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at            : Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes                   : Mapped[Optional[str]]     = mapped_column(Text)

    # Relaciones
    branch     : Mapped["Branch"]           = relationship("Branch", back_populates="missions")
    receiver   : Mapped["Receiver"]         = relationship("Receiver", back_populates="missions")
    volunteer  : Mapped[Optional["Volunteer"]] = relationship("Volunteer", back_populates="missions")
    handshakes : Mapped[list["Handshake"]]  = relationship("Handshake", back_populates="mission")

    __table_args__ = (
        CheckConstraint("quantity_units > 0", name="missions_quantity_positive"),
        Index("idx_missions_branch_status", "branch_id", "status"),
        Index("idx_missions_expires", "expires_at"),
        Index("idx_missions_volunteer_id", "volunteer_id"),
    )


# ── Tabla 8: Handshakes ───────────────────────────────────────────────────────
class Handshake(RepresentableMixin, Base):
    __tablename__ = "handshakes"

    id               : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id       : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)
    handshake_number : Mapped[int]       = mapped_column(Integer, nullable=False)
    actor_type       : Mapped[ActorType] = mapped_column(SAEnum(ActorType), nullable=False)
    actor_id         : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    hmac_signature   : Mapped[str]       = mapped_column(String(64), nullable=False)
    latitude         : Mapped[float]     = mapped_column(Numeric(10, 7), nullable=False)
    longitude        : Mapped[float]     = mapped_column(Numeric(10, 7), nullable=False)
    geofence_valid   : Mapped[bool]      = mapped_column(Boolean, nullable=False)
    signed_at        : Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    mission : Mapped["Mission"] = relationship("Mission", back_populates="handshakes")

    __table_args__ = (
        CheckConstraint("handshake_number IN (1, 2)", name="handshakes_number_valid"),
        UniqueConstraint("mission_id", "handshake_number", name="uq_handshake_per_mission"),
    )


# ── Tabla 9: Log de TrustPoints ───────────────────────────────────────────────
class TrustPointsLog(RepresentableMixin, Base):
    __tablename__ = "trust_points_log"

    id            : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    volunteer_id  : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("volunteers.id"), nullable=False)
    mission_id    : Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("missions.id"))
    delta         : Mapped[int]       = mapped_column(Integer, nullable=False)
    reason        : Mapped[str]       = mapped_column(String(100), nullable=False)
    balance_after : Mapped[int]       = mapped_column(Integer, nullable=False)
    created_at    : Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relaciones
    volunteer : Mapped["Volunteer"] = relationship("Volunteer", back_populates="trust_points_log")

    __table_args__ = (
        Index("idx_trust_points_log_volunteer_id", "volunteer_id"),
    )


# ── Tabla 10: Reportes Fiscales ───────────────────────────────────────────────
class FiscalReport(TimestampMixin, RepresentableMixin, Base):
    __tablename__ = "fiscal_reports"

    id                  : Mapped[uuid.UUID]         = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id           : Mapped[uuid.UUID]         = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    period_start        : Mapped[datetime]          = mapped_column(DateTime(timezone=True), nullable=False)
    period_end          : Mapped[datetime]          = mapped_column(DateTime(timezone=True), nullable=False)
    total_missions      : Mapped[int]               = mapped_column(Integer, nullable=False, default=0)
    total_weight_kg     : Mapped[float]             = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_units         : Mapped[int]               = mapped_column(Integer, nullable=False, default=0)
    declared_value_mxn  : Mapped[float]             = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_deduction_mxn   : Mapped[float]             = mapped_column(Numeric(12, 2), nullable=False, default=0)
    report_status       : Mapped[ReportStatus]      = mapped_column(SAEnum(ReportStatus), nullable=False, default=ReportStatus.draft)
    aviso39_data        : Mapped[Optional[dict]]    = mapped_column(JSONB)
    submitted_at        : Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relaciones
    branch : Mapped["Branch"] = relationship("Branch", back_populates="fiscal_reports")

    __table_args__ = (
        UniqueConstraint("branch_id", "period_start", "period_end", name="uq_fiscal_report_period"),
    )
