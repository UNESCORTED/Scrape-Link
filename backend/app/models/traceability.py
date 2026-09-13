import uuid
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TraceabilityRecord(Base):
    __tablename__ = "traceability_records"

    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("material_lots.lot_id"))
    photo_refs: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric)
    gps_location: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False))
    captured_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    handover_reference_number: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    recycler_confirmed: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    recycler_confirmed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    status_history: Mapped[list | None] = mapped_column(JSONB, server_default=text("'[]'"))
