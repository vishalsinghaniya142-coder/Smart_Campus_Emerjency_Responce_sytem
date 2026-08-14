from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.dependencies import get_current_user


router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_200_OK,
)
async def analyze_image(
    file: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Image-analysis API contract.

    POST /image-analysis

    Member 2:
        Receives and validates the authenticated upload.

    Member 3:
        Provides the actual Vision/AI image analysis.
    """

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is required.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image filename is required.",
        )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported image type. "
                "Use JPEG, PNG, or WEBP."
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Image analysis AI service is not connected yet. "
            "Connect Member 3 vision service."
        ),
    )