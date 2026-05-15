from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from api.deps import get_covenant_handler, get_facility_type_header
from business.covenant import CovenantHandler
from business.enums import FacilityType
from schemas.covenant import CovenantResult
from schemas.error import ErrorResponse

router = APIRouter()


@router.post(
    "/calculate",
    response_model=CovenantResult,
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
) -> CovenantResult:
    """Calculate the covenant result for the declared facility payload.

    Args:
        request: Incoming HTTP request containing the raw payload body.
        facility_type: Facility declared through the request header.
        covenant_handler: Business handler that performs the calculation.

    Returns:
        CovenantResult: Calculated covenant response for the payload.
    """

    return covenant_handler.calculate(
        facility_type=facility_type,
        payload=await request.body(),
    )
