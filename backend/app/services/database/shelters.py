from app.services.database.firebase_client import db


SHELTERS_COLLECTION = "shelters"


def create_shelter(shelter_id, data):
    """Create a new shelter in Firestore."""

    db.collection(SHELTERS_COLLECTION).document(shelter_id).set(data)

    return {
        "id": shelter_id,
        **data
    }


def get_shelter(shelter_id):
    """Get a shelter from Firestore."""

    doc = db.collection(SHELTERS_COLLECTION).document(shelter_id).get()

    if not doc.exists:
        return None

    return {
        "id": doc.id,
        **doc.to_dict()
    }