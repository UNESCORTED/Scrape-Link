from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import ensure_collector_access, ensure_recycler_access, extract_point
from app.core.auth import Principal, get_current_principal
from app.db.session import get_db_session
from app.models.material_lot import MaterialLot
from app.models.traceability import TraceabilityRecord
from app.models.transaction import Transaction
from app.schemas.sync import SyncBatchRequest, SyncBatchResponse, SyncRecordResult

router = APIRouter(prefix="/sync", tags=["sync"])


def _same_record(
    existing: Any,
    incoming: dict[str, Any],
    ignored: set[str] | None = None,
) -> bool:
    ignored = ignored or set()

    for key, value in incoming.items():
        if key in ignored:
            continue

        if not hasattr(existing, key):
            return False

        if getattr(existing, key) != value:
            return False

    return True


@router.post(
    "/batch",
    response_model=SyncBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def sync_batch(
    payload: SyncBatchRequest,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> SyncBatchResponse:
    results: list[SyncRecordResult] = []

    # ---------------------------------------------------------
    # LOTS
    # ---------------------------------------------------------
    for lot_payload in payload.lots:
        ensure_collector_access(principal, lot_payload.collector_id)

        data = lot_payload.model_dump()
        lot_id = lot_payload.lot_id

        location_wkt = extract_point(data, "collection_location")
        if location_wkt:
            data["collection_location"] = func.ST_GeogFromText(location_wkt)

        existing = await session.get(MaterialLot, lot_id)

        if existing is not None:
            if _same_record(
                existing,
                data,
                ignored={"collection_location"},
            ):
                results.append(
                    SyncRecordResult(
                        record_type="lot",
                        client_id=str(lot_id),
                        server_id=str(lot_id),
                        status="duplicate",
                        detail="Lot already exists with the same data.",
                    )
                )
            else:
                results.append(
                    SyncRecordResult(
                        record_type="lot",
                        client_id=str(lot_id),
                        server_id=str(lot_id),
                        status="conflict",
                        detail="Lot already exists with different data.",
                    )
                )

            continue

        session.add(MaterialLot(**data))
        await session.flush()

        results.append(
            SyncRecordResult(
                record_type="lot",
                client_id=str(lot_id),
                server_id=str(lot_id),
                status="accepted",
            )
        )

    # ---------------------------------------------------------
    # TRANSACTIONS
    # ---------------------------------------------------------
    for transaction_payload in payload.transactions:
        if transaction_payload.transaction_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="transaction_id is required for offline synchronization.",
            )

        if transaction_payload.collector_id is not None:
            ensure_collector_access(
                principal,
                transaction_payload.collector_id,
            )

        if transaction_payload.recycler_id is not None:
            ensure_recycler_access(
                principal,
                transaction_payload.recycler_id,
            )

        data = transaction_payload.model_dump(exclude_none=True)
        transaction_id = transaction_payload.transaction_id

        handover_wkt = extract_point(data, "handover_location")
        if handover_wkt:
            data["handover_location"] = func.ST_GeogFromText(handover_wkt)

        existing = await session.get(Transaction, transaction_id)

        if existing is not None:
            if _same_record(
                existing,
                data,
                ignored={"handover_location"},
            ):
                results.append(
                    SyncRecordResult(
                        record_type="transaction",
                        client_id=str(transaction_id),
                        server_id=str(transaction_id),
                        status="duplicate",
                        detail="Transaction already exists with the same data.",
                    )
                )
            else:
                results.append(
                    SyncRecordResult(
                        record_type="transaction",
                        client_id=str(transaction_id),
                        server_id=str(transaction_id),
                        status="conflict",
                        detail="Transaction already exists with different data.",
                    )
                )

            continue

        session.add(Transaction(**data))
        await session.flush()

        results.append(
            SyncRecordResult(
                record_type="transaction",
                client_id=str(transaction_id),
                server_id=str(transaction_id),
                status="accepted",
            )
        )

    # ---------------------------------------------------------
    # TRACEABILITY
    # ---------------------------------------------------------
    for trace_payload in payload.traceability_records:
        if trace_payload.trace_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="trace_id is required for offline synchronization.",
            )

        if trace_payload.lot_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="lot_id is required for traceability synchronization.",
            )

        lot = await session.get(
            MaterialLot,
            trace_payload.lot_id,
        )

        if lot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lot not found for traceability record.",
            )

        ensure_collector_access(
            principal,
            lot.collector_id,
        )

        data = trace_payload.model_dump(exclude_none=True)
        trace_id = trace_payload.trace_id

        gps_wkt = extract_point(data, "gps_location")
        if gps_wkt:
            data["gps_location"] = func.ST_GeogFromText(gps_wkt)

        handover_statement = select(TraceabilityRecord).where(
            TraceabilityRecord.handover_reference_number
            == trace_payload.handover_reference_number
        )

        handover_result = await session.execute(handover_statement)
        handover_existing = handover_result.scalar_one_or_none()

        if (
            handover_existing is not None
            and handover_existing.trace_id != trace_id
        ):
            results.append(
                SyncRecordResult(
                    record_type="traceability",
                    client_id=str(trace_id),
                    server_id=str(handover_existing.trace_id),
                    status="conflict",
                    detail=(
                        "Handover reference number is already linked "
                        "to another traceability record."
                    ),
                )
            )

            continue

        existing = await session.get(
            TraceabilityRecord,
            trace_id,
        )

        if existing is not None:
            if _same_record(
                existing,
                data,
                ignored={"gps_location"},
            ):
                results.append(
                    SyncRecordResult(
                        record_type="traceability",
                        client_id=str(trace_id),
                        server_id=str(trace_id),
                        status="duplicate",
                        detail=(
                            "Traceability record already exists "
                            "with the same data."
                        ),
                    )
                )
            else:
                results.append(
                    SyncRecordResult(
                        record_type="traceability",
                        client_id=str(trace_id),
                        server_id=str(trace_id),
                        status="conflict",
                        detail=(
                            "Traceability record already exists "
                            "with different data."
                        ),
                    )
                )

            continue

        session.add(
            TraceabilityRecord(**data)
        )

        await session.flush()

        results.append(
            SyncRecordResult(
                record_type="traceability",
                client_id=str(trace_id),
                server_id=str(trace_id),
                status="accepted",
            )
        )

    await session.commit()

    return SyncBatchResponse(results=results)