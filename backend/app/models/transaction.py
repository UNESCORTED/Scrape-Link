import uuid
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("payment_mode IN ('cash','digital')", name="transactions_payment_mode_check"),
        CheckConstraint("payment_status IN ('pending','paid','partial')", name="transactions_payment_status_check"),
        CheckConstraint(
            "transaction_status IN ('initiated','handed_over','confirmed','completed','flagged')",
            name="transactions_transaction_status_check",
        ),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("material_lots.lot_id"))
    collector_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("collectors.collector_id"))
    recycler_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("recyclers.recycler_id"))
    quoted_price: Mapped[Decimal | None] = mapped_column(Numeric)
    final_price: Mapped[Decimal | None] = mapped_column(Numeric)
    payment_mode: Mapped[str | None] = mapped_column(Text, server_default=text("'cash'"))
    payment_status: Mapped[str | None] = mapped_column(Text, server_default=text("'pending'"))
    transaction_status: Mapped[str | None] = mapped_column(Text, server_default=text("'initiated'"))
    handover_location: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False))
    handover_timestamp: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
