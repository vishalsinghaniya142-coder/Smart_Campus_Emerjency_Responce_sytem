from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user
from app.services.database.firebase_client import db


router = APIRouter(tags=["Notifications"])


def serialize_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Firestore timestamp values into JSON-safe strings."""

    serialized = dict(data)
    for key, value in serialized.items():
        if hasattr(value, "isoformat"):
            serialized[key] = value.isoformat()
    return serialized


@router.get("", response_model=Dict[str, Any])
async def list_notifications(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
) -> Dict[str, Any]:
    """Return recent shared emergency notifications for logged-in users."""

    documents = list(db.collection("notifications").stream())
    documents.sort(
        key=lambda document: str(document.to_dict().get("created_at", "")),
        reverse=True,
    )

    notifications = [
        serialize_notification({"id": document.id, **document.to_dict()})
        for document in documents[:limit]
    ]
    return {"success": True, "data": notifications}