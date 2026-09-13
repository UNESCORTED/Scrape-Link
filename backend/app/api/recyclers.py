from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import clean_update, commit_refresh, ensure_recycler_access, extract_point, json_ready
from app.core.auth import Principal, get_current_principal
from app.db.session import get_db_session
from app.models.material_lot import MaterialLot
from app.models.recycler import Recycler
from app.schemas.matching import RecyclerMatchResponse
from app.schemas.recyclers import RecyclerCreate, RecyclerResponse, RecyclerUpdate
from app.services.matching_service import ranked_recycler_matches


router = APIRouter(prefix="/recyclers", tags=["recyclers"])


@router.post("", response_model=RecyclerResponse, status_code=status.HTTP_201_CREATED)
async def create_recycler(
    payload: RecyclerCreate,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> Recycler:
    data = payload.model_dump()
    location_wkt = extract_point(data, "facility_location")
    data["offered_rates"] = json_ready(data.get("offered_rates"))
    recycler = Recycler(**data)
    if location_wkt:
        recycler.facility_location = func.ST_GeogFromText(location_wkt)
    session.add(recycler)
    return await commit_refresh(session, recycler)


@router.get("", response_model=list[RecyclerResponse])
async def list_recyclers(session: AsyncSession = Depends(get_db_session)) -> list[Recycler]:
    result = await session.execute(select(Recycler).order_by(Recycler.created_at.desc()))
    return list(result.scalars().all())


@router.get("/match", response_model=list[RecyclerMatchResponse])
async def match_recyclers(
    lot_id: UUID,
    limit: int = 10,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> list[dict]:
    lot = await session.get(MaterialLot, lot_id)
    if lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")
    if principal.role == "collector" and principal.collector_id != lot.collector_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Collector cannot match this lot")
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="limit must be between 1 and 50")
    return await ranked_recycler_matches(session, lot, limit=limit)


@router.get("/{recycler_id}", response_model=RecyclerResponse)
async def get_recycler(recycler_id: UUID, session: AsyncSession = Depends(get_db_session)) -> Recycler:
    recycler = await session.get(Recycler, recycler_id)
    if recycler is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recycler not found")
    return recycler


@router.patch("/{recycler_id}", response_model=RecyclerResponse)
async def update_recycler(
    recycler_id: UUID,
    payload: RecyclerUpdate,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> Recycler:
    ensure_recycler_access(principal, recycler_id)
    recycler = await session.get(Recycler, recycler_id)
    if recycler is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recycler not found")
    data = payload.model_dump(exclude_unset=True)
    location_wkt = extract_point(data, "facility_location")
    if "offered_rates" in data:
        data["offered_rates"] = json_ready(data["offered_rates"])
    for key, value in clean_update(data).items():
        setattr(recycler, key, value)
    if location_wkt:
        recycler.facility_location = func.ST_GeogFromText(location_wkt)
    recycler.updated_at = func.now()
    return await commit_refresh(session, recycler)
