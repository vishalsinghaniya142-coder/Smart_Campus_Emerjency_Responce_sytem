from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.cloud.firestore_v1.base_query import FieldFilter

from app.services.database.firebase_client import db
from app.models.user import UserAuthentication


USERS_COLLECTION = "users"


class FirebaseUserRepository:
    """
    Firebase/Firestore implementation of the UserRepository contract.

    This class uses the existing Firestore connection from
    firebase_client.py. No new Firebase connection is created here.
    """

    def __init__(self):
        self.collection = db.collection(USERS_COLLECTION)

    # ========================================================
    # CREATE USER
    # ========================================================

    async def create_user(
        self,
        user: UserAuthentication,
    ) -> UserAuthentication:
        """
        Store a new authenticated user in Firestore.
        """

        user_data = {
    "id": user.id,
    "name": user.name,
    "email": str(user.email),
    "phone_number": user.phone_number,
    "password_hash": user.password_hash,
    "role": user.role,
    "credits": user.credits,
    "is_active": user.is_active,
    "is_verified": user.is_verified,
    "created_at": user.created_at,
    "updated_at": user.updated_at,
}

        self.collection.document(user.id).set(user_data)

        return user

    # ========================================================
    # GET USER BY EMAIL
    # ========================================================

    async def get_user_by_email(
        self,
        email: str,
    ) -> Optional[UserAuthentication]:
        """
        Find a user in Firestore using email.
        """

        normalized_email = email.strip().lower()

        query = (
            self.collection
            .where(
                filter=FieldFilter(
                    "email",
                    "==",
                    normalized_email,
                ),
            )
            .limit(1)
            .stream()
        )

        documents = list(query)

        if not documents:
            return None

        document = documents[0]

        data = document.to_dict()

        return self._document_to_user(
            document.id,
            data,
        )

    @staticmethod
    def _normalize_phone_number(phone_number: str) -> str:
        """Normalize a stored phone value for reliable lookup."""

        if phone_number is None:
            return ""

        cleaned = "".join(ch for ch in str(phone_number).strip() if ch.isdigit() or ch == "+")

        if cleaned.startswith("00"):
            cleaned = "+" + cleaned[2:]

        return cleaned

    async def get_user_by_phone_number(
        self,
        phone_number: str,
    ) -> Optional[UserAuthentication]:
        """Find a user in Firestore using their phone number."""

        if not phone_number:
            return None

        normalized_phone = self._normalize_phone_number(phone_number)
        candidate_values = {normalized_phone}

        if normalized_phone.startswith("+"):
            candidate_values.add(normalized_phone[1:])
        else:
            candidate_values.add(f"+{normalized_phone}")

        for candidate in sorted(candidate_values, key=len):
            if not candidate:
                continue

            documents = list(
                self.collection
                .where(
                    filter=FieldFilter(
                        "phone_number",
                        "==",
                        candidate,
                    ),
                )
                .limit(1)
                .stream()
            )

            if documents:
                document = documents[0]
                return self._document_to_user(
                    document.id,
                    document.to_dict(),
                )

        return None

    async def list_active_users(self) -> list[UserAuthentication]:
        """Return active users whose registered phone can receive SOS SMS."""

        documents = self.collection.where(
            filter=FieldFilter("is_active", "==", True),
        ).stream()

        return [
            self._document_to_user(document.id, document.to_dict())
            for document in documents
        ]

    # ========================================================
    # GET USER BY ID
    # ========================================================

    async def get_user_by_id(
        self,
        user_id: str,
    ) -> Optional[UserAuthentication]:

        # 1. Try document ID
        document = (
            self.collection
            .document(user_id)
            .get()
        )

        if document.exists:
            return self._document_to_user(
                document.id,
                document.to_dict(),
            )

        # 2. Fallback for existing documents
        documents = list(
            self.collection
            .where(
                filter=FieldFilter(
                    "id",
                    "==",
                    user_id,
                ),
            )
            .limit(1)
            .stream()
        )

        if documents:
            document = documents[0]

            return self._document_to_user(
                document.id,
                document.to_dict(),
            )

        return None
    # ========================================================
    # UPDATE USER
    # ========================================================

    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Optional[UserAuthentication]:
        """
        Update an existing user in Firestore.
        """

        document_ref = (
            self.collection
            .document(user_id)
        )

        document = document_ref.get()

        if not document.exists:
            return None

        update_data = dict(updates)

        if "email" in update_data:
            update_data["email"] = (
                str(update_data["email"])
                .strip()
                .lower()
            )

        if "updated_at" not in update_data:
            update_data["updated_at"] = (
                datetime.now(timezone.utc)
            )

        document_ref.update(update_data)

        updated_document = document_ref.get()

        if not updated_document.exists:
            return None

        return self._document_to_user(
            updated_document.id,
            updated_document.to_dict(),
        )

    # ========================================================
    # DELETE USER
    # ========================================================

    async def delete_user(
        self,
        user_id: str,
    ) -> bool:
        """
        Delete a user from Firestore.
        """

        document_ref = (
            self.collection
            .document(user_id)
        )

        document = document_ref.get()

        if not document.exists:
            return False

        document_ref.delete()

        return True

    # ========================================================
    # FIRESTORE DOCUMENT → USER MODEL
    # ========================================================

    @staticmethod
    def _document_to_user(
        user_id: str,
        data: Dict[str, Any],
    ) -> UserAuthentication:
        """
        Convert a Firestore document into UserAuthentication.
        """

        created_at = data.get(
            "created_at"
        )

        updated_at = data.get(
            "updated_at"
        )

        # Firestore timestamps can be converted to datetime.
        if hasattr(created_at, "replace"):
            created_at = created_at.replace(
                tzinfo=timezone.utc
            ) if created_at.tzinfo is None else created_at

        if hasattr(updated_at, "replace"):
            updated_at = updated_at.replace(
                tzinfo=timezone.utc
            ) if updated_at.tzinfo is None else updated_at

        # Safety fallback for older documents.
        if created_at is None:
            created_at = datetime.now(
                timezone.utc
            )

        if updated_at is None:
            updated_at = created_at

        return UserAuthentication(
            id=user_id,
            name=data.get(
                "name",
                "",
            ),
            email=data.get(
                "email",
                "",
            ),
            phone_number=data.get(
                "phone_number",
                "",
            ),
            password_hash=data.get(
                "password_hash",
                "",
            ),
            role=data.get(
                "role",
                "student",
            ),
            credits=int(data.get("credits", 0) or 0),
            is_active=data.get(
                "is_active",
                True,
            ),
            is_verified=data.get(
                "is_verified",
                False,
            ),
            created_at=created_at,
            updated_at=updated_at,
        )