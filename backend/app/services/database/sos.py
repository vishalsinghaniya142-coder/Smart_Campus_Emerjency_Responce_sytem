from app.services.database.firebase_client import db


SOS_COLLECTION = "sos"


def create_sos(sos_id, data):
    """Create a new SOS request in Firestore."""

    db.collection(SOS_COLLECTION).document(sos_id).set(data)

    return {
        "id": sos_id,
        **data
    }


def get_sos(sos_id):
    """Get an SOS request from Firestore."""

    doc = db.collection(SOS_COLLECTION).document(sos_id).get()

    if not doc.exists:
        return None

    return {
        "id": doc.id,
        **doc.to_dict()
    }