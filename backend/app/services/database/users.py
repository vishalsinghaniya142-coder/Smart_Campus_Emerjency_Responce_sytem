from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.services.database.firebase_client import (
    get_firestore_client,
)


USERS_COLLECTION = "users"


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    user_id: str,
    name: str,
    email: Optional[str],
    role: str = "student",
    phone_number: Optional[str] = None,
    provider: Optional[str] = None,
    is_verified: bool = False,
):

    db = get_firestore_client()

    now = datetime.now(
        timezone.utc
    )


    user_data = {

        "name": name,

        "email": email,

        "phone_number": phone_number,

        "role": role,

        "provider": provider,

        "is_active": True,

        "is_verified": is_verified,

        "created_at": now,

        "updated_at": now,
    }


    db.collection(
        USERS_COLLECTION
    ).document(
        user_id
    ).set(
        user_data,
        merge=True,
    )


    return {
        "id": user_id,
        **user_data,
    }


# ============================================================
# GET USER
# ============================================================

def get_user(
    user_id: str,
):

    db = get_firestore_client()

    document = (
        db.collection(
            USERS_COLLECTION
        )
        .document(
            user_id
        )
        .get()
    )


    if not document.exists:

        return None


    return {
        "id": document.id,
        **document.to_dict(),
    }


# ============================================================
# GET USER BY EMAIL
# ============================================================

def get_user_by_email(
    email: str,
):

    db = get_firestore_client()

    documents = (
        db.collection(
            USERS_COLLECTION
        )
        .where(
            "email",
            "==",
            email,
        )
        .limit(1)
        .stream()
    )


    for document in documents:

        return {
            "id": document.id,
            **document.to_dict(),
        }


    return None


# ============================================================
# GET USER BY PHONE
# ============================================================

def get_user_by_phone(
    phone_number: str,
):

    db = get_firestore_client()

    documents = (
        db.collection(
            USERS_COLLECTION
        )
        .where(
            "phone_number",
            "==",
            phone_number,
        )
        .limit(1)
        .stream()
    )


    for document in documents:

        return {
            "id": document.id,
            **document.to_dict(),
        }


    return None


# ============================================================
# UPDATE USER
# ============================================================

def update_user(
    user_id: str,
    data: Dict[str, Any],
):

    db = get_firestore_client()


    updates = dict(data)

    updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )


    db.collection(
        USERS_COLLECTION
    ).document(
        user_id
    ).set(
        updates,
        merge=True,
    )


    return get_user(
        user_id
    )


# ============================================================
# UPSERT FIREBASE USER
# ============================================================

def upsert_firebase_user(
    firebase_uid: str,
    name: str,
    email: Optional[str],
    phone_number: Optional[str],
    provider: str,
    is_verified: bool,
    role: str = "student",
):

    existing_user = get_user(
        firebase_uid
    )


    if existing_user is None:

        return create_user(
            user_id=firebase_uid,
            name=name,
            email=email,
            phone_number=phone_number,
            role=role,
            provider=provider,
            is_verified=is_verified,
        )


    updates = {

        "name": name,

        "email": email,

        "phone_number": phone_number,

        "provider": provider,

        "is_verified": is_verified,

        "is_active": existing_user.get(
            "is_active",
            True,
        ),

        "role": existing_user.get(
            "role",
            role,
        ),
    }


    return update_user(
        firebase_uid,
        updates,
    )


# ============================================================
# DELETE USER
# ============================================================

def delete_user(
    user_id: str,
):

    db = get_firestore_client()

    (
        db.collection(
            USERS_COLLECTION
        )
        .document(
            user_id
        )
        .delete()
    )

    return True