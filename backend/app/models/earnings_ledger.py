import uuid
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EarningsLedger(Base):
    __tablename__ = "earnings_ledger"
    __table_args__ = (
        CheckConstraint("entry_type IN ('earned','paid','pending_due')", name="earnings_ledger_entry_type_check"),
    )

    entry_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    collector_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("collectors.collector_id"))
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.transaction_id"))
    amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    entry_type: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
