from typing import Any, Dict, Optional

from app.services.database.firebase_client import db


def get_data(collection: str, document_id: str) -> Optional[Dict[str, Any]]:
    """Get a document from Firestore."""

    doc_ref = db.collection(collection).document(document_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()

    return None


def save_data(
    collection: str,
    document_id: str,
    data: Dict[str, Any],
) -> bool:
    """Create or replace a Firestore document."""

    db.collection(collection).document(document_id).set(data)
    return True


def update_data(
    collection: str,
    document_id: str,
    data: Dict[str, Any],
) -> bool:
    """Update an existing Firestore document."""

    db.collection(collection).document(document_id).update(data)
    return True


def delete_data(
    collection: str,
    document_id: str,
) -> bool:
    """Delete a Firestore document."""

    db.collection(collection).document(document_id).delete()
    return True