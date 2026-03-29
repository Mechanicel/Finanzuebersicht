from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from finanzuebersicht_shared.models import ApiResponse

from app.dependencies import get_person_service
from app.models import (
    AllowanceListResponse,
    AllowanceSummaryResponse,
    AssignmentListResponse,
    Person,
    PersonBankAssignment,
    PersonCreate,
    PersonDetailResponse,
    PersonListResponse,
    PersonSortField,
    PersonUpdate,
    SortDirection,
    TaxAllowance,
)
from app.services.person_service import PersonService

router = APIRouter(tags=["persons"])


@router.get("/persons", response_model=ApiResponse[PersonListResponse])
async def list_persons(
    q: str | None = Query(default=None, description="Suchbegriff für Vorname/Nachname/E-Mail"),
    sort_by: PersonSortField = Query(default=PersonSortField.LAST_NAME),
    direction: SortDirection = Query(default=SortDirection.ASC),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: PersonService = Depends(get_person_service),
) -> ApiResponse[PersonListResponse]:
    return ApiResponse(
        data=service.list_persons(q=q, sort_by=sort_by, direction=direction, limit=limit, offset=offset)
    )


@router.post("/persons", response_model=ApiResponse[Person], status_code=status.HTTP_201_CREATED)
async def create_person(payload: PersonCreate, service: PersonService = Depends(get_person_service)) -> ApiResponse[Person]:
    return ApiResponse(data=service.create_person(payload))


@router.get("/persons/{person_id}", response_model=ApiResponse[PersonDetailResponse])
async def get_person(person_id: UUID, service: PersonService = Depends(get_person_service)) -> ApiResponse[PersonDetailResponse]:
    return ApiResponse(data=service.get_person_detail(person_id))


@router.patch("/persons/{person_id}", response_model=ApiResponse[Person])
async def patch_person(
    person_id: UUID,
    payload: PersonUpdate,
    service: PersonService = Depends(get_person_service),
) -> ApiResponse[Person]:
    return ApiResponse(data=service.update_person(person_id, payload))


@router.delete("/persons/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(person_id: UUID, service: PersonService = Depends(get_person_service)) -> Response:
    service.delete_person(person_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/persons/{person_id}/banks", response_model=ApiResponse[AssignmentListResponse])
async def list_person_banks(
    person_id: UUID,
    service: PersonService = Depends(get_person_service),
) -> ApiResponse[AssignmentListResponse]:
    return ApiResponse(data=service.list_assignments(person_id))


@router.post(
    "/persons/{person_id}/banks/{bank_id}",
    response_model=ApiResponse[PersonBankAssignment],
    status_code=status.HTTP_201_CREATED,
)
async def create_person_bank_assignment(
    person_id: UUID,
    bank_id: UUID,
    service: PersonService = Depends(get_person_service),
) -> ApiResponse[PersonBankAssignment]:
    return ApiResponse(data=service.create_assignment(person_id, bank_id))


@router.delete("/persons/{person_id}/banks/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person_bank_assignment(
    person_id: UUID,
    bank_id: UUID,
    service: PersonService = Depends(get_person_service),
) -> Response:
    service.delete_assignment(person_id, bank_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/persons/{person_id}/allowances", response_model=ApiResponse[AllowanceListResponse])
async def list_allowances(
    person_id: UUID,
    service: PersonService = Depends(get_person_service),
) -> ApiResponse[AllowanceListResponse]:
    return ApiResponse(data=service.list_allowances(person_id))


@router.put("/persons/{person_id}/allowances/{bank_id}", response_model=ApiResponse[TaxAllowance])
async def put_allowance(
    person_id: UUID,
    bank_id: UUID,
    amount: Decimal = Query(ge=Decimal("0"), decimal_places=2),
    service: PersonService = Depends(get_person_service),
) -> ApiResponse[TaxAllowance]:
    return ApiResponse(data=service.upsert_allowance(person_id, bank_id, amount))


@router.get("/persons/{person_id}/allowances/summary", response_model=ApiResponse[AllowanceSummaryResponse])
async def allowance_summary(
    person_id: UUID,
    service: PersonService = Depends(get_person_service),
) -> ApiResponse[AllowanceSummaryResponse]:
    return ApiResponse(data=service.allowance_summary(person_id))
