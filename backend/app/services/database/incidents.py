from app.services.database.firebase_client import db


INCIDENTS_COLLECTION = "incidents"


def create_incident(incident_id, data):
    """Create a new emergency incident."""

    db.collection(INCIDENTS_COLLECTION).document(incident_id).set(data)

    return {
        "id": incident_id,
        **data
    }


def get_incident(incident_id):
    """Get an incident from Firestore."""

    doc = db.collection(INCIDENTS_COLLECTION).document(incident_id).get()

    if not doc.exists:
        return None

    return {
        "id": doc.id,
        **doc.to_dict()
    }