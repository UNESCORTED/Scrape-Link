import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)
Role = Literal["collector", "recycler"]
_otp_store: dict[str, tuple[str, float]] = {}


@dataclass(frozen=True)
class Principal:
    role: Role
    subject: str
    collector_id: UUID | None = None
    recycler_id: UUID | None = None


def hash_phone_number(phone_number: str) -> str:
    normalized = "".join(ch for ch in phone_number if ch.isdigit() or ch == "+")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def issue_mock_otp(phone_number: str, settings: Settings) -> str:
    otp = "123456" if settings.mock_otp_enabled else f"{secrets.randbelow(1_000_000):06d}"
    _otp_store[phone_number] = (otp, time.time() + 300)
    logger.info("Mock OTP for %s is %s", phone_number, otp)
    return otp


def verify_mock_otp(phone_number: str, otp: str) -> bool:
    stored = _otp_store.get(phone_number)
    if stored is None:
        return False
    expected_otp, expires_at = stored
    if time.time() > expires_at:
        _otp_store.pop(phone_number, None)
        return False
    if not hmac.compare_digest(expected_otp, otp):
        return False
    _otp_store.pop(phone_number, None)
    return True


def _urlsafe_json(data: dict) -> bytes:
    return base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":"), default=str).encode("utf-8")).rstrip(b"=")


def _urlsafe_decode(value: str) -> dict:
    padded = value + "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")))


def create_access_token(principal: Principal, settings: Settings) -> str:
    payload = {
        "role": principal.role,
        "sub": principal.subject,
        "collector_id": str(principal.collector_id) if principal.collector_id else None,
        "recycler_id": str(principal.recycler_id) if principal.recycler_id else None,
        "exp": int(time.time()) + settings.access_token_ttl_seconds,
    }
    payload_bytes = _urlsafe_json(payload)
    signature = hmac.new(settings.app_secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"{payload_bytes.decode('utf-8')}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode('utf-8')}"


def decode_access_token(token: str, settings: Settings) -> Principal:
    try:
        payload_part, signature_part = token.split(".", 1)
        expected_signature = hmac.new(
            settings.app_secret_key.encode("utf-8"),
            payload_part.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        padded_signature = signature_part + "=" * (-len(signature_part) % 4)
        provided_signature = base64.urlsafe_b64decode(padded_signature.encode("utf-8"))
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("bad signature")
        payload = _urlsafe_decode(payload_part)
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("expired token")
        role = payload["role"]
        if role not in {"collector", "recycler"}:
            raise ValueError("invalid role")
        return Principal(
            role=role,
            subject=payload["sub"],
            collector_id=UUID(payload["collector_id"]) if payload.get("collector_id") else None,
            recycler_id=UUID(payload["recycler_id"]) if payload.get("recycler_id") else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return decode_access_token(credentials.credentials, settings)


def require_role(*roles: Role):
    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return dependency
