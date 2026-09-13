import uuid
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MaterialLot(Base):
    __tablename__ = "material_lots"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','listed','matched','handed_over','completed','disputed')",
            name="material_lots_status_check",
        ),
        CheckConstraint(
            "sync_status IN ('pending','synced','conflict')",
            name="material_lots_sync_status_check",
        ),
    )

    lot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    collector_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("collectors.collector_id"))
    material_category: Mapped[str] = mapped_column(Text, nullable=False)
    sub_category: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    image_ref: Mapped[str | None] = mapped_column(Text)
    approx_weight_kg: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    condition: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(Text)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric)
    quoted_price: Mapped[Decimal | None] = mapped_column(Numeric)
    final_sale_value: Mapped[Decimal | None] = mapped_column(Numeric)
    collection_location: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False))
    collection_timestamp: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(Text, server_default=text("'draft'"))
    sync_status: Mapped[str | None] = mapped_column(Text, server_default=text("'pending'"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
