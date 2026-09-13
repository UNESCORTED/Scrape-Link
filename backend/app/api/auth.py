from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import Principal, create_access_token, hash_phone_number, issue_mock_otp, verify_mock_otp
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.collector import Collector
from app.models.recycler import Recycler
from app.schemas.auth import AuthTokenResponse, OTPRequest, OTPRequestResponse, OTPVerifyRequest


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-otp", response_model=OTPRequestResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_otp(payload: OTPRequest, settings: Settings = Depends(get_settings)) -> OTPRequestResponse:
    otp = issue_mock_otp(payload.phone_number, settings)
    return OTPRequestResponse(
        message="OTP generated for local/demo authentication",
        dev_otp=otp if settings.mock_otp_enabled else None,
    )


@router.post("/verify-otp", response_model=AuthTokenResponse)
async def verify_otp(
    payload: OTPVerifyRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AuthTokenResponse:
    if not verify_mock_otp(payload.phone_number, payload.otp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")

    phone_hash = hash_phone_number(payload.phone_number)
    collector_id = None
    recycler_id = None

    if payload.role == "collector":
        result = await session.execute(select(Collector).where(Collector.phone_number_hash == phone_hash))
        collector = result.scalar_one_or_none()
        if collector is None:
            collector = Collector(phone_number_hash=phone_hash, preferred_language=payload.preferred_language)
            session.add(collector)
            await session.commit()
            await session.refresh(collector)
        collector_id = collector.collector_id
    else:
        if payload.recycler_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="recycler_id is required for recycler login")
        recycler = await session.get(Recycler, payload.recycler_id)
        if recycler is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recycler not found")
        recycler_id = recycler.recycler_id

    principal = Principal(
        role=payload.role,
        subject=phone_hash,
        collector_id=collector_id,
        recycler_id=recycler_id,
    )
    return AuthTokenResponse(
        access_token=create_access_token(principal, settings),
        role=payload.role,
        collector_id=collector_id,
        recycler_id=recycler_id,
    )
