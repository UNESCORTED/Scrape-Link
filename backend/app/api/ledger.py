from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import ensure_collector_access
from app.core.auth import Principal, get_current_principal
from app.db.session import get_db_session
from app.models.earnings_ledger import EarningsLedger
from app.schemas.ledger import LedgerEntryResponse


router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/{collector_id}", response_model=list[LedgerEntryResponse])
async def get_collector_ledger(
    collector_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> list[EarningsLedger]:
    ensure_collector_access(principal, collector_id)
    result = await session.execute(
        select(EarningsLedger)
        .where(EarningsLedger.collector_id == collector_id)
        .order_by(EarningsLedger.created_at.desc())
    )
    return list(result.scalars().all())
