from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.schemas.prediction_schema import (
    PredictionAPIResponse,
    PredictionRequest,
    build_prediction_response,
    prediction_request_to_data,
)
from app.services.prediction_service import predict_pincode_risk


router = APIRouter()


class LocationPredictionRequest(BaseModel):
    location: str = Field(..., min_length=2, max_length=120)


@router.post(
    "",
    response_model=PredictionAPIResponse,
    status_code=status.HTTP_200_OK,
)
async def create_prediction(
    payload: PredictionRequest,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> PredictionAPIResponse:
    """
    Prediction API contract.

    POST /prediction

    Member 2 responsibility:
        Receive and validate the request.

    Member 3 responsibility:
        Actual prediction/risk/severity AI logic.

    Until Member 3 is connected, this endpoint returns
    a clear service-unavailable response instead of
    inventing prediction logic.
    """

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    # --------------------------------------------------------
    # AI service will be connected here later.
    # --------------------------------------------------------

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Prediction AI service is not connected yet. "
            "Connect Member 3 prediction service."
        ),
    )


@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
)
async def analyze_location_prediction(
    payload: LocationPredictionRequest,
) -> dict[str, Any]:
    """Resolve a pincode and run the existing risk engine on live data."""

    try:
        return await predict_pincode_risk(payload.location)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (requests.RequestException, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Real prediction service unavailable: {exc}",
        ) from exc