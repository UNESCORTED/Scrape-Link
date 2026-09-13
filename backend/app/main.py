from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api import auth, ledger, lots, prices, recyclers, sync, traceability, transactions
from app.core.config import get_settings


settings = get_settings()


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Database constraint conflict"},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Database operation failed"},
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(lots.router, prefix=settings.api_v1_prefix)
app.include_router(prices.router, prefix=settings.api_v1_prefix)
app.include_router(recyclers.router, prefix=settings.api_v1_prefix)
app.include_router(transactions.router, prefix=settings.api_v1_prefix)
app.include_router(traceability.router, prefix=settings.api_v1_prefix)
app.include_router(ledger.router, prefix=settings.api_v1_prefix)
app.include_router(sync.router, prefix=settings.api_v1_prefix)
