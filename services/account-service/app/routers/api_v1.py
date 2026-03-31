from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_account_service
from app.models import PersonAccount, PersonAccountCreate, PersonAccountUpdate
from app.services.account_service import AccountService

router = APIRouter(tags=["accounts"])


@router.get("/persons/{person_id}/accounts", response_model=ApiResponse[list[PersonAccount]])
async def list_person_accounts(
    person_id: UUID,
    service: AccountService = Depends(get_account_service),
) -> ApiResponse[list[PersonAccount]]:
    return ApiResponse(data=service.list_person_accounts(person_id))


@router.get("/persons/{person_id}/accounts/{account_id}", response_model=ApiResponse[PersonAccount])
async def get_person_account(
    person_id: UUID,
    account_id: UUID,
    service: AccountService = Depends(get_account_service),
) -> ApiResponse[PersonAccount]:
    return ApiResponse(data=service.get_person_account(person_id, account_id))


@router.post("/persons/{person_id}/accounts", response_model=ApiResponse[PersonAccount], status_code=status.HTTP_201_CREATED)
async def create_person_account(
    person_id: UUID,
    payload: PersonAccountCreate,
    service: AccountService = Depends(get_account_service),
) -> ApiResponse[PersonAccount]:
    return ApiResponse(data=service.create_person_account(person_id, payload))


@router.patch("/persons/{person_id}/accounts/{account_id}", response_model=ApiResponse[PersonAccount])
async def patch_person_account(
    person_id: UUID,
    account_id: UUID,
    payload: PersonAccountUpdate,
    service: AccountService = Depends(get_account_service),
) -> ApiResponse[PersonAccount]:
    return ApiResponse(data=service.update_person_account(person_id, account_id, payload))
