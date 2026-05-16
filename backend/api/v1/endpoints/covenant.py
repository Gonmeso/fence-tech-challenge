from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from api.deps import get_covenant_handler, get_facility_type_header
from business.covenant import CovenantHandler
from business.enums import FacilityType
from schemas.covenant import CovenantPublishedResult, OnChainCovenantResult
from schemas.error import ErrorResponse

router = APIRouter()


@router.post(
    "/calculate",
    response_model=CovenantPublishedResult,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
async def calculate_covenant(
    request: Request,
    facility_type: Annotated[FacilityType, Depends(get_facility_type_header)],
    covenant_handler: Annotated[CovenantHandler, Depends(get_covenant_handler)],
) -> CovenantPublishedResult:
    """Calculate and publish the covenant result for the declared facility.

    Args:
        request: Incoming HTTP request containing the raw payload body.
        facility_type: Facility declared through the request header.
        covenant_handler: Business handler that performs the calculation.

    Returns:
        CovenantPublishedResult: Calculated covenant response with transaction metadata.
    """

    return await covenant_handler.calculate_and_publish(
        facility_type=facility_type,
        payload=await request.body(),
    )


@router.get(
    "/result",
    response_model=OnChainCovenantResult,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
async def get_covenant_result(
    facility_type: Annotated[FacilityType, Depends(get_facility_type_header)],
    covenant_handler: Annotated[CovenantHandler, Depends(get_covenant_handler)],
) -> OnChainCovenantResult:
    """Read the latest on-chain covenant result for the declared facility.

    Args:
        facility_type: Facility declared through the request header.
        covenant_handler: Business handler that reads from the registry.

    Returns:
        OnChainCovenantResult: Latest published covenant result.
    """

    return await covenant_handler.get_published_result(facility_type=facility_type)
