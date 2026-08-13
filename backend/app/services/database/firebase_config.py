import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials


# Project root:
# Smart_Campus_Emergency_Response_system/
BASE_DIR = Path(__file__).resolve().parents[3]

# Firebase service-account credentials folder
CREDENTIALS_DIR = BASE_DIR / "credentials"


def initialize_firebase():
    """
    Initialize Firebase Admin SDK.

    The service-account JSON file should be placed inside:
    Smart_Campus_Emergency_Response_system/credentials/
    """

    # If Firebase is already initialized, don't initialize it again
    if firebase_admin._apps:
        return firebase_admin.get_app()

    # Find JSON files inside credentials folder
    json_files = list(CREDENTIALS_DIR.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(
            f"No Firebase service-account JSON file found in: {CREDENTIALS_DIR}"
        )

    if len(json_files) > 1:
        raise RuntimeError(
            f"Multiple JSON files found in {CREDENTIALS_DIR}. "
            "Keep only the Firebase service-account JSON file there."
        )

    credential_file = json_files[0]

    print(f"Using Firebase credentials: {credential_file.name}")

    cred = credentials.Certificate(str(credential_file))

    app = firebase_admin.initialize_app(
        cred,
        {
            "projectId": "smart-campus-ai-emergency"
        }
    )

    print("Firebase initialized successfully!")

    return app