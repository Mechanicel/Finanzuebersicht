from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from finanzuebersicht_shared import create_app

from app.config import get_settings
from app.dependencies import get_gateway_service
from app.routers import api_v1_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(api_v1_router)
    return router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # startup — nothing required; the AsyncClient is created lazily on first request
    yield
    # shutdown — release the shared connection pool (5.1)
    service = get_gateway_service()
    await service.aclose()


def create_application():
    settings = get_settings()
    return create_app(settings=settings, api_router=build_api_router(), lifespan=_lifespan)
