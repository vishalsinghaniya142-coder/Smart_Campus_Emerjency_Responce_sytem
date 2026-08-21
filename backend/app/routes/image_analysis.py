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

    image_bytes = await file.read()
    max_size = 10 * 1024 * 1024
    if len(image_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image must be 10 MB or smaller.",
        )

    filename = file.filename.lower()
    visual_keywords = {
        "fire": ("severe", 0.9, "Filename indicates a possible fire scene."),
        "smoke": ("high", 0.75, "Filename indicates a possible smoke scene."),
        "flood": ("high", 0.75, "Filename indicates a possible flood scene."),
        "accident": ("high", 0.75, "Filename indicates a possible accident scene."),
        "medical": ("high", 0.75, "Filename indicates a possible medical emergency."),
    }
    risk, confidence, reason = ("moderate", 0.35, "Image received; professional review is recommended.")
    for keyword, result in visual_keywords.items():
        if keyword in filename:
            risk, confidence, reason = result
            break

    return {
        "success": True,
        "analysis_mode": "baseline",
        "filename": file.filename,
        "risk_level": risk,
        "confidence": confidence,
        "reason": reason,
        "next_step": "Connect a vision model for pixel-level image analysis.",
    }