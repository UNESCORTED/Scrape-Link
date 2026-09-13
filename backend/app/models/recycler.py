import uuid
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import ARRAY, Boolean, CheckConstraint, DateTime, Index, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Recycler(Base):
    __tablename__ = "recyclers"
    __table_args__ = (
        CheckConstraint(
            "authorization_status IN ('authorized','pending','unverified','suspended')",
            name="recyclers_authorization_status_check",
        ),
        Index("idx_recyclers_location", "facility_location", postgresql_using="gist"),
    )

    recycler_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    facility_location: Mapped[object] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False)
    service_area_radius_km: Mapped[Decimal | None] = mapped_column(Numeric, server_default=text("15"))
    materials_accepted: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    authorization_id: Mapped[str | None] = mapped_column(Text)
    authorization_status: Mapped[str | None] = mapped_column(Text)
    contact_phone: Mapped[str | None] = mapped_column(Text)
    offered_rates: Mapped[dict | None] = mapped_column(JSONB)
    pickup_available: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
