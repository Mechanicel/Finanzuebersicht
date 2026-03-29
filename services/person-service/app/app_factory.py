from __future__ import annotations

from fastapi import APIRouter
from finanzuebersicht_shared import create_app

from app.config import get_settings
from app.routers import api_v1_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(api_v1_router)
    return router


def create_application():
    settings = get_settings()
    return create_app(settings=settings, api_router=build_api_router())
