from typing import Any, Dict, Optional

from app.models.user import UserAuthentication
from app.services.database.firebase_client import db


USERS_COLLECTION = "users"


# ============================================================
# FIREBASE USER REPOSITORY
# ============================================================

class FirebaseUserRepository:
    """
    Firebase Firestore implementation of the UserRepository.

    This repository is responsible for persisting users in
    Firebase Firestore.

    Collection:
        users
    """

    # ========================================================
    # CREATE USER
    # ========================================================

    async def create_user(
        self,
        user: UserAuthentication,
    ) -> UserAuthentication:
        """
        Create a new user in Firestore.
        """

        user_data = {
            "id": user.id,
            "name": user.name,
            "email": str(user.email).strip().lower(),
            "password_hash": user.password_hash,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        db.collection(
            USERS_COLLECTION
        ).document(
            user.id
        ).set(
            user_data
        )

        return user

    # ========================================================
    # GET USER BY EMAIL
    # ========================================================

    async def get_user_by_email(
        self,
        email: str,
    ) -> Optional[UserAuthentication]:
        """
        Find a user by email address.
        """

        documents = (
            db.collection(
                USERS_COLLECTION
            )
            .where(
                "email",
                "==",
                email.strip().lower(),
            )
            .limit(1)
            .stream()
        )

        for document in documents:

            data = document.to_dict()

            return UserAuthentication(
                id=data["id"],
                name=data["name"],
                email=data["email"],
                password_hash=data["password_hash"],
                role=data.get(
                    "role",
                    "student",
                ),
                is_active=data.get(
                    "is_active",
                    True,
                ),
                is_verified=data.get(
                    "is_verified",
                    False,
                ),
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )

        return None

    # ========================================================
    # GET USER BY ID
    # ========================================================

    async def get_user_by_id(
        self,
        user_id: str,
    ) -> Optional[UserAuthentication]:
        """
        Find a user by Firestore document ID.
        """

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

        data = document.to_dict()

        return UserAuthentication(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            password_hash=data["password_hash"],
            role=data.get(
                "role",
                "student",
            ),
            is_active=data.get(
                "is_active",
                True,
            ),
            is_verified=data.get(
                "is_verified",
                False,
            ),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    # ========================================================
    # UPDATE USER
    # ========================================================

    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Optional[UserAuthentication]:
        """
        Update an existing user.
        """

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

        db.collection(
            USERS_COLLECTION
        ).document(
            user_id
        ).update(
            updates
        )

        return await self.get_user_by_id(
            user_id
        )

    # ========================================================
    # DELETE USER
    # ========================================================

    async def delete_user(
        self,
        user_id: str,
    ) -> bool:
        """
        Delete an existing user.
        """

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
            return False

        db.collection(
            USERS_COLLECTION
        ).document(
            user_id
        ).delete()

        return True


# ============================================================
# LEGACY CRUD FUNCTIONS
# ============================================================
# Kept so existing backend modules using the old helpers
# continue to work.
# ============================================================

def create_user(
    user_id,
    name,
    email,
    role="student",
    password_hash=None,
    is_active=True,
    is_verified=False,
    created_at=None,
    updated_at=None,
):
    """
    Legacy helper for creating a user directly in Firestore.
    """

    user_data = {
        "id": user_id,
        "name": name,
        "email": str(email).strip().lower(),
        "role": role,
        "is_active": is_active,
        "is_verified": is_verified,
    }

    if password_hash is not None:
        user_data["password_hash"] = password_hash

    if created_at is not None:
        user_data["created_at"] = created_at

    if updated_at is not None:
        user_data["updated_at"] = updated_at

    db.collection(
        USERS_COLLECTION
    ).document(
        user_id
    ).set(
        user_data
    )

    return {
        "id": user_id,
        **user_data,
    }


def get_user(
    user_id,
):
    """
    Legacy helper for getting a user from Firestore.
    """

    document = (
        db.collection(
            USERS_COLLECTION
        )
        .document(
            user_id
        )
        .get()
    )

    if document.exists:
        return {
            "id": document.id,
            **document.to_dict(),
        }

    return None


def update_user(
    user_id,
    data,
):
    """
    Legacy helper for updating a user.
    """

    db.collection(
        USERS_COLLECTION
    ).document(
        user_id
    ).update(
        data
    )

    return get_user(
        user_id
    )


def delete_user(
    user_id,
):
    """
    Legacy helper for deleting a user.
    """

    db.collection(
        USERS_COLLECTION
    ).document(
        user_id
    ).delete()

    return True