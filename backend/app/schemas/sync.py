from pydantic import BaseModel, Field

from app.schemas.lots import LotCreate
from app.schemas.traceability import TraceabilityCreate
from app.schemas.transactions import TransactionCreate


class SyncBatchRequest(BaseModel):
    lots: list[LotCreate] = Field(default_factory=list)
    transactions: list[TransactionCreate] = Field(default_factory=list)
    traceability_records: list[TraceabilityCreate] = Field(default_factory=list)


class SyncRecordResult(BaseModel):
    record_type: str
    client_id: str | None = None
    server_id: str | None = None
    status: str
    detail: str | None = None


class SyncBatchResponse(BaseModel):
    results: list[SyncRecordResult]
