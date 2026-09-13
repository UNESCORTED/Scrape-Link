import uuid
from datetime import date
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import BigInteger, Date, ForeignKey, Index, Numeric, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("idx_price_category_date", "material_category", "recorded_date"),
    )

    price_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    material_category: Mapped[str] = mapped_column(Text, nullable=False)
    sub_category: Mapped[str | None] = mapped_column(Text)
    location: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False))
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False)
    buying_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    market_range_min: Mapped[Decimal | None] = mapped_column(Numeric)
    market_range_max: Mapped[Decimal | None] = mapped_column(Numeric)
    unit: Mapped[str | None] = mapped_column(Text, server_default=text("'kg'"))
    recycler_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("recyclers.recycler_id"))
    source: Mapped[str | None] = mapped_column(Text)
