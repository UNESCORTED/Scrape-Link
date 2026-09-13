from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import clean_update, commit_refresh, ensure_collector_access, extract_point
from app.core.auth import Principal, get_current_principal
from app.db.session import get_db_session
from app.models.material_lot import MaterialLot
from app.schemas.classification import LotClassificationResponse
from app.schemas.lots import LotCreate, LotResponse, LotUpdate
from app.services.classification_service import classify_lot as classify_lot_with_service
from app.services.valuation_service import estimate_lot_value


router = APIRouter(prefix="/lots", tags=["lots"])


@router.post("", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
async def create_lot(
    payload: LotCreate,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> MaterialLot:
    ensure_collector_access(principal, payload.collector_id)
    data = payload.model_dump()
    location_wkt = extract_point(data, "collection_location")
    lot = MaterialLot(**data)
    if location_wkt:
        lot.collection_location = func.ST_GeogFromText(location_wkt)
    session.add(lot)
    return await commit_refresh(session, lot)


@router.get("", response_model=list[LotResponse])
async def list_lots(
    collector_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> list[MaterialLot]:
    ensure_collector_access(principal, collector_id)
    statement = select(MaterialLot).order_by(MaterialLot.created_at.desc())
    if collector_id:
        statement = statement.where(MaterialLot.collector_id == collector_id)
    result = await session.execute(statement)
    return list(result.scalars().all())


@router.get("/{lot_id}", response_model=LotResponse)
async def get_lot(
    lot_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> MaterialLot:
    lot = await session.get(MaterialLot, lot_id)
    if lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")
    ensure_collector_access(principal, lot.collector_id)
    return lot


@router.post("/{lot_id}/classify", response_model=LotClassificationResponse)
async def classify_lot(
    lot_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> LotClassificationResponse:
    lot = await session.get(MaterialLot, lot_id)
    if lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")
    ensure_collector_access(principal, lot.collector_id)
    classification = await classify_lot_with_service(lot)
    valuation = await estimate_lot_value(session, lot)
    if valuation.estimated_value is not None:
        lot.estimated_value = valuation.estimated_value
        lot.updated_at = func.now()
        await session.commit()
    return LotClassificationResponse(
        lot_id=lot.lot_id,
        material_category=classification.material_category,
        category_confidence=classification.confidence,
        estimated_value=valuation.estimated_value,
        unit_price=valuation.unit_price,
        valuation_method=valuation.method,
        classification_method=classification.method,
    )


@router.patch("/{lot_id}", response_model=LotResponse)
async def update_lot(
    lot_id: UUID,
    payload: LotUpdate,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> MaterialLot:
    lot = await session.get(MaterialLot, lot_id)
    if lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")
    ensure_collector_access(principal, lot.collector_id)
    data = payload.model_dump(exclude_unset=True)
    location_wkt = extract_point(data, "collection_location")
    for key, value in clean_update(data).items():
        setattr(lot, key, value)
    if location_wkt:
        lot.collection_location = func.ST_GeogFromText(location_wkt)
    lot.updated_at = func.now()
    return await commit_refresh(session, lot)
