from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import clean_update, commit_refresh, ensure_collector_access, ensure_recycler_access, extract_point
from app.core.auth import Principal, get_current_principal
from app.db.session import get_db_session
from app.models.transaction import Transaction
from app.schemas.transactions import TransactionCreate, TransactionResponse, TransactionUpdate


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> Transaction:
    ensure_collector_access(principal, payload.collector_id)
    ensure_recycler_access(principal, payload.recycler_id)
    data = payload.model_dump(exclude_none=True)
    location_wkt = extract_point(data, "handover_location")
    transaction = Transaction(**data)
    if location_wkt:
        transaction.handover_location = func.ST_GeogFromText(location_wkt)
    session.add(transaction)
    return await commit_refresh(session, transaction)


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    collector_id: UUID | None = None,
    recycler_id: UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> list[Transaction]:
    ensure_collector_access(principal, collector_id)
    ensure_recycler_access(principal, recycler_id)
    statement = select(Transaction).order_by(Transaction.created_at.desc())
    if collector_id:
        statement = statement.where(Transaction.collector_id == collector_id)
    if recycler_id:
        statement = statement.where(Transaction.recycler_id == recycler_id)
    result = await session.execute(statement)
    return list(result.scalars().all())


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> Transaction:
    transaction = await session.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    ensure_collector_access(principal, transaction.collector_id)
    ensure_recycler_access(principal, transaction.recycler_id)
    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    payload: TransactionUpdate,
    session: AsyncSession = Depends(get_db_session),
    principal: Principal = Depends(get_current_principal),
) -> Transaction:
    transaction = await session.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    ensure_collector_access(principal, transaction.collector_id)
    ensure_recycler_access(principal, transaction.recycler_id)
    data = payload.model_dump(exclude_unset=True)
    location_wkt = extract_point(data, "handover_location")
    for key, value in clean_update(data).items():
        setattr(transaction, key, value)
    if location_wkt:
        transaction.handover_location = func.ST_GeogFromText(location_wkt)
    return await commit_refresh(session, transaction)
