from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# PREDICTION REQUEST
# ============================================================

class PredictionRequest(BaseModel):
    """
    Request contract for:

        POST /prediction

    IMPORTANT:
        The PDF defines the prediction endpoint but does not
        specify the exact prediction input fields.

        Therefore this schema keeps the AI input as a validated
        dictionary instead of inventing Member 3's model fields.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    input_data: Dict[str, Any] = Field(
        ...,
        description="Input data forwarded to the prediction service.",
    )


# ============================================================
# PREDICTION RESPONSE
# ============================================================

class PredictionResponse(BaseModel):
    """
    Response contract for prediction.

    The actual prediction/risk/severity logic belongs to
    Member 3's AI/ML module.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    result: Any = Field(
        ...,
        description="Prediction result returned by the AI service.",
    )

    risk: Optional[Any] = Field(
        default=None,
        description="Risk information when provided by the AI service.",
    )

    severity: Optional[Any] = Field(
        default=None,
        description="Severity information when provided by the AI service.",
    )


# ============================================================
# PREDICTION API RESPONSE
# ============================================================

class PredictionAPIResponse(BaseModel):
    """
    Standard API wrapper for POST /prediction.
    """

    success: bool = True

    message: str = (
        "Prediction generated successfully."
    )

    data: PredictionResponse


# ============================================================
# PREDICTION INPUT CONVERTER
# ============================================================

def prediction_request_to_data(
    payload: PredictionRequest,
) -> Dict[str, Any]:
    """
    Convert the FastAPI request schema into data that can be
    passed to the prediction service.
    """

    return {
        "input_data": payload.input_data,
    }


# ============================================================
# PREDICTION RESPONSE BUILDER
# ============================================================

def build_prediction_response(
    result: Any,
    risk: Optional[Any] = None,
    severity: Optional[Any] = None,
) -> PredictionAPIResponse:
    """
    Build the backend response after the prediction service
    returns its result.
    """

    prediction = PredictionResponse(
        result=result,
        risk=risk,
        severity=severity,
    )

    return PredictionAPIResponse(
        success=True,
        message=(
            "Prediction generated successfully."
        ),
        data=prediction,
    )