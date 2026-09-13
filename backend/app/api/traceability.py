from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import commit_refresh, extract_point
from app.core.auth import Principal, get_current_principal, require_role
from app.db.session import get_db_session
from app.models.traceability import TraceabilityRecord
from app.schemas.traceability import TraceabilityConfirm, TraceabilityCreate, TraceabilityResponse


router = APIRouter(prefix="/traceability", tags=["traceability"])


@router.post("", response_model=TraceabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_traceability_record(
    payload: TraceabilityCreate,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> TraceabilityRecord:
    data = payload.model_dump(exclude_none=True)
    gps_wkt = extract_point(data, "gps_location")
    record = TraceabilityRecord(**data, recycler_confirmed=False)
    if gps_wkt:
        record.gps_location = func.ST_GeogFromText(gps_wkt)
    session.add(record)
    return await commit_refresh(session, record)


@router.get("/{trace_id}", response_model=TraceabilityResponse)
async def get_traceability_record(
    trace_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> TraceabilityRecord:
    record = await session.get(TraceabilityRecord, trace_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Traceability record not found")
    return record


@router.post("/{trace_id}/confirm", response_model=TraceabilityResponse)
async def confirm_traceability_record(
    trace_id: UUID,
    payload: TraceabilityConfirm,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(require_role("recycler")),
) -> TraceabilityRecord:
    record = await session.get(TraceabilityRecord, trace_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Traceability record not found")
    confirmed_at = payload.recycler_confirmed_at or datetime.now(timezone.utc)
    record.recycler_confirmed = True
    record.recycler_confirmed_at = confirmed_at
    status_history = list(record.status_history or [])
    status_history.append(
        {
            "status": payload.status_note,
            "at": confirmed_at.isoformat(),
            "actor_role": principal.role,
            "actor_id": str(principal.recycler_id) if principal.recycler_id else None,
        }
    )
    record.status_history = status_history
    return await commit_refresh(session, record)


@router.get("", response_model=list[TraceabilityResponse])
async def list_traceability_records(
    lot_id: UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> list[TraceabilityRecord]:
    statement = select(TraceabilityRecord)
    if lot_id:
        statement = statement.where(TraceabilityRecord.lot_id == lot_id)
    result = await session.execute(statement)
    return list(result.scalars().all())
