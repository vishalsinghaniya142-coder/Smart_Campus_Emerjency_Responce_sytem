from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user


router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_200_OK,
)
async def chatbot(
    payload: dict[str, Any],
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Chatbot API contract.

    POST /chatbot

    Member 2:
        Receives authenticated chatbot requests.

    Member 3:
        Provides the actual Gemini/AI chatbot implementation.
    """

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chatbot request.",
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Chatbot AI service is not connected yet. "
            "Connect Member 3 chatbot service."
        ),
    )