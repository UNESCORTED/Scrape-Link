import uuid

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Collector(Base):
    __tablename__ = "collectors"
    __table_args__ = (
        CheckConstraint("preferred_language IN ('hi','mr','en')", name="collectors_preferred_language_check"),
    )

    collector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    phone_number_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    preferred_language: Mapped[str] = mapped_column(Text, server_default=text("'hi'"))
    operating_area: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
