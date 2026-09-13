from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import ensure_collector_access, ensure_recycler_access, extract_point
from app.core.auth import Principal, get_current_principal
from app.db.session import get_db_session
from app.models.material_lot import MaterialLot
from app.models.traceability import TraceabilityRecord
from app.models.transaction import Transaction
from app.schemas.sync import SyncBatchRequest, SyncBatchResponse, SyncRecordResult


router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/batch", response_model=SyncBatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def sync_batch(
    payload: SyncBatchRequest,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> SyncBatchResponse:
    results: list[SyncRecordResult] = []

    for lot_payload in payload.lots:
        ensure_collector_access(principal, lot_payload.collector_id)
        data = lot_payload.model_dump()
        location_wkt = extract_point(data, "collection_location")
        if location_wkt:
            data["collection_location"] = func.ST_GeogFromText(location_wkt)
        statement = insert(MaterialLot).values(**data).on_conflict_do_nothing(index_elements=["lot_id"])
        await session.execute(statement)
        results.append(SyncRecordResult(record_type="lot", client_id=str(lot_payload.lot_id), server_id=str(lot_payload.lot_id), status="accepted"))

    for transaction_payload in payload.transactions:
        ensure_collector_access(principal, transaction_payload.collector_id)
        ensure_recycler_access(principal, transaction_payload.recycler_id)
        data = transaction_payload.model_dump(exclude_none=True)
        transaction_id = data.get("transaction_id")
        location_wkt = extract_point(data, "handover_location")
        if location_wkt:
            data["handover_location"] = func.ST_GeogFromText(location_wkt)
        statement = insert(Transaction).values(**data)
        if transaction_id:
            statement = statement.on_conflict_do_nothing(index_elements=["transaction_id"])
        await session.execute(statement)
        results.append(SyncRecordResult(record_type="transaction", client_id=str(transaction_id) if transaction_id else None, server_id=str(transaction_id) if transaction_id else None, status="accepted"))

    for trace_payload in payload.traceability_records:
        data = trace_payload.model_dump(exclude_none=True)
        trace_id = data.get("trace_id")
        gps_wkt = extract_point(data, "gps_location")
        if gps_wkt:
            data["gps_location"] = func.ST_GeogFromText(gps_wkt)
        statement = insert(TraceabilityRecord).values(**data).on_conflict_do_nothing(index_elements=["handover_reference_number"])
        await session.execute(statement)
        results.append(SyncRecordResult(record_type="traceability", client_id=str(trace_id) if trace_id else None, server_id=str(trace_id) if trace_id else None, status="accepted"))

    await session.commit()
    return SyncBatchResponse(results=results)
