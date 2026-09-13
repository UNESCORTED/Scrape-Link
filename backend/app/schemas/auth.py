from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)
    role: Literal["collector", "recycler"] = "collector"
    preferred_language: Literal["hi", "mr", "en"] = "hi"
    recycler_id: UUID | None = None


class OTPRequestResponse(BaseModel):
    message: str
    dev_otp: str | None = None


class OTPVerifyRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)
    otp: str = Field(min_length=4, max_length=8)
    role: Literal["collector", "recycler"] = "collector"
    preferred_language: Literal["hi", "mr", "en"] = "hi"
    recycler_id: UUID | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Literal["collector", "recycler"]
    collector_id: UUID | None = None
    recycler_id: UUID | None = None
