from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_masterdata_service
from app.models import (
    AccountType,
    AccountTypeCreate,
    AccountTypeListResponse,
    AccountTypeUpdate,
    Bank,
    BankCreate,
    BankListResponse,
    BankUpdate,
)
from app.services.masterdata_service import MasterdataService

router = APIRouter(tags=["masterdata"])


@router.get("/banks", response_model=ApiResponse[BankListResponse])
async def list_banks(service: MasterdataService = Depends(get_masterdata_service)) -> ApiResponse[BankListResponse]:
    return ApiResponse(data=service.list_banks())


@router.post("/banks", response_model=ApiResponse[Bank], status_code=status.HTTP_201_CREATED)
async def create_bank(
    payload: BankCreate,
    service: MasterdataService = Depends(get_masterdata_service),
) -> ApiResponse[Bank]:
    return ApiResponse(data=service.create_bank(payload))


@router.get("/banks/{bank_id}", response_model=ApiResponse[Bank])
async def get_bank(bank_id: UUID, service: MasterdataService = Depends(get_masterdata_service)) -> ApiResponse[Bank]:
    return ApiResponse(data=service.get_bank(bank_id))


@router.patch("/banks/{bank_id}", response_model=ApiResponse[Bank])
async def patch_bank(
    bank_id: UUID,
    payload: BankUpdate,
    service: MasterdataService = Depends(get_masterdata_service),
) -> ApiResponse[Bank]:
    return ApiResponse(data=service.update_bank(bank_id, payload))


@router.delete("/banks/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank(bank_id: UUID, service: MasterdataService = Depends(get_masterdata_service)) -> Response:
    service.delete_bank(bank_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/account-types", response_model=ApiResponse[AccountTypeListResponse])
async def list_account_types(
    service: MasterdataService = Depends(get_masterdata_service),
) -> ApiResponse[AccountTypeListResponse]:
    return ApiResponse(data=service.list_account_types())


@router.post("/account-types", response_model=ApiResponse[AccountType], status_code=status.HTTP_201_CREATED)
async def create_account_type(
    payload: AccountTypeCreate,
    service: MasterdataService = Depends(get_masterdata_service),
) -> ApiResponse[AccountType]:
    return ApiResponse(data=service.create_account_type(payload))


@router.get("/account-types/{account_type_id}", response_model=ApiResponse[AccountType])
async def get_account_type(
    account_type_id: UUID,
    service: MasterdataService = Depends(get_masterdata_service),
) -> ApiResponse[AccountType]:
    return ApiResponse(data=service.get_account_type(account_type_id))


@router.patch("/account-types/{account_type_id}", response_model=ApiResponse[AccountType])
async def patch_account_type(
    account_type_id: UUID,
    payload: AccountTypeUpdate,
    service: MasterdataService = Depends(get_masterdata_service),
) -> ApiResponse[AccountType]:
    return ApiResponse(data=service.update_account_type(account_type_id, payload))


@router.delete("/account-types/{account_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account_type(
    account_type_id: UUID,
    service: MasterdataService = Depends(get_masterdata_service),
) -> Response:
    service.delete_account_type(account_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
