from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud.firestore_v1.base_query import FieldFilter

from app.services.database.firebase_client import db

from app.models.sos import (
    SOS,
    sos_from_document,
    sos_to_document,
)


SOS_COLLECTION = "sos"


def _normalize_legacy_sos(data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    data.setdefault("status", "active")
    data.setdefault("message", None)
    data.setdefault("created_at", now)
    data.setdefault("updated_at", data["created_at"])
    return data


class FirebaseSOSRepository:
    """Firebase Firestore implementation for SOSRepository."""

    async def create_sos(self, sos: SOS) -> SOS:
        data = sos_to_document(sos)

        db.collection(SOS_COLLECTION).document(
            sos.id
        ).set(data)

        return sos

    async def get_sos_by_id(
        self,
        sos_id: str,
    ) -> Optional[SOS]:

        doc = (
            db.collection(SOS_COLLECTION)
            .document(sos_id)
            .get()
        )

        if not doc.exists:
            return None

        data = doc.to_dict() or {}
        data["id"] = doc.id

        return sos_from_document(_normalize_legacy_sos(data))

    async def list_sos_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SOS]:

        query = (
            db.collection(SOS_COLLECTION)
            .where(
                filter=FieldFilter(
                    "user_id",
                    "==",
                    user_id,
                ),
            )
            .limit(limit + offset)
        )

        documents = list(query.stream())

        documents = documents[offset:offset + limit]

        results = []

        for doc in documents:
            data = doc.to_dict() or {}
            data["id"] = doc.id

            results.append(
                sos_from_document(_normalize_legacy_sos(data))
            )

        return results

    async def update_sos(
        self,
        sos_id: str,
        updates: Dict[str, Any],
    ) -> Optional[SOS]:

        doc_ref = (
            db.collection(SOS_COLLECTION)
            .document(sos_id)
        )

        doc = doc_ref.get()

        if not doc.exists:
            return None

        doc_ref.update(updates)

        updated_doc = doc_ref.get()

        data = updated_doc.to_dict() or {}
        data["id"] = updated_doc.id

        return sos_from_document(_normalize_legacy_sos(data))


# ------------------------------------------------------------
# Legacy helper functions
# ------------------------------------------------------------

def create_sos(sos_id, data):
    """Create a new SOS request in Firestore."""

    db.collection(SOS_COLLECTION).document(
        sos_id
    ).set(data)

    return {
        "id": sos_id,
        **data,
    }


def get_sos(sos_id):
    """Get an SOS request from Firestore."""

    doc = (
        db.collection(SOS_COLLECTION)
        .document(sos_id)
        .get()
    )

    if not doc.exists:
        return None

    return {
        "id": doc.id,
        **doc.to_dict(),
    }