from app.services.database.firebase_client import db


USERS_COLLECTION = "users"


def create_user(user_id, name, email, role="student"):
    """Create a new user in Firestore."""

    user_data = {
        "name": name,
        "email": email,
        "role": role,
    }

    db.collection(USERS_COLLECTION).document(user_id).set(user_data)

    return {
        "id": user_id,
        **user_data
    }


def get_user(user_id):
    """Get a user from Firestore."""

    document = (
        db.collection(USERS_COLLECTION)
        .document(user_id)
        .get()
    )

    if document.exists:
        return {
            "id": document.id,
            **document.to_dict()
        }

    return None


def update_user(user_id, data):
    """Update an existing user."""

    db.collection(USERS_COLLECTION).document(user_id).update(data)

    return get_user(user_id)


def delete_user(user_id):
    """Delete a user from Firestore."""

    db.collection(USERS_COLLECTION).document(user_id).delete()

    return True