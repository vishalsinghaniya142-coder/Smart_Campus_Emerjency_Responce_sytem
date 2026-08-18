from app.services.config.environment import get_env


FIREBASE_PROJECT_ID = get_env("FIREBASE_PROJECT_ID")
FIREBASE_CREDENTIALS_PATH = get_env("FIREBASE_CREDENTIALS_PATH")


def get_firebase_settings():
    """
    Return Firebase configuration settings.
    """
    return {
        "project_id": FIREBASE_PROJECT_ID,
        "credentials_path": FIREBASE_CREDENTIALS_PATH,
    }