"""
================================================================================
Smart Campus Emergency Response System — AI Module (SINGLE FILE VERSION)
================================================================================

This file merges the entire ai/ package (chatbot, vision, prediction,
fake_alert, emergency, config, utils) into ONE importable module, so it
can be dropped straight into a FastAPI backend without worrying about
folder structure or import paths.

PUBLIC FUNCTIONS (what your backend should import and call):

    from ai_module import process_message
    from ai_module import analyze_image
    from ai_module import predict_risk
    from ai_module import detect_fake_alert
    from ai_module import generate_emergency_response

Every public function returns a plain dict — FastAPI serializes it to
JSON automatically. Every function is safe to call even if GEMINI_API_KEY
is not set: it falls back to deterministic, rule-based logic instead of
crashing.

SETUP
-----
    pip install google-genai pydantic python-dotenv pillow

    # Optional — only needed for AI-powered chatbot/vision replies.
    # Without it, chatbot + vision still work using safe fallbacks.
    Create a .env file next to this one with:
        GEMINI_API_KEY=your_key_here
        GEMINI_MODEL=gemini-1.5-flash
        GEMINI_VISION_MODEL=gemini-1.5-flash
        AI_TEMPERATURE=0.4

SAFETY NOTES
------------
- This module never claims emergency services were contacted.
- Vision results never claim certainty ("possible fire detected", not
  "this is a fire").
- Fake-alert results are only ever classified as verified /
  needs_verification / suspicious — never declared definitively fake.
- Emergency instructions come from a static, human-reviewed list first.
================================================================================
"""

from __future__ import annotations

import json
import os
from functools import wraps
from typing import Any, Callable, Optional

from dotenv import load_dotenv
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, field_validator

load_dotenv()


# ==============================================================================
# SECTION 1: SETTINGS  (was: ai/config/ai_settings.py)
# ==============================================================================

MODEL_NAME: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
VISION_MODEL_NAME: str = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-flash")
DEFAULT_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.4"))
MAX_RESPONSE_LENGTH: int = 800

MAX_IMAGE_SIZE_MB: float = 8.0
SUPPORTED_IMAGE_TYPES: set[str] = {"jpg", "jpeg", "png", "webp"}

EMERGENCY_TYPES: list[str] = ["fire", "earthquake", "medical", "flood", "chemical", "crowd", "unknown"]
SEVERITY_LEVELS: list[str] = ["low", "medium", "high", "critical"]


# ==============================================================================
# SECTION 2: ERROR HANDLING  (was: ai/utils/error_handler.py)
# ==============================================================================

class AIError(Exception):
    """Base class for all AI-module errors."""


class AIConfigurationError(AIError):
    """Raised when required configuration (e.g. GEMINI_API_KEY) is missing."""


class InvalidInputError(AIError):
    """Raised when a caller passes invalid or incomplete input data."""


class ImageProcessingError(AIError):
    """Raised when an uploaded image fails validation or cannot be opened."""


class GeminiUnavailableError(AIError):
    """Raised when a call to the Gemini API fails, times out, or errors."""


class ResponseParsingError(AIError):
    """Raised when Gemini's response cannot be parsed into the expected schema."""


def safe_ai_call(fallback_factory: Callable[[Exception], dict]):
    """
    Decorator for public AI functions. Catches AIError (and any
    unexpected exception) and returns a safe error dict instead of
    letting the exception crash the caller.
    """
    def decorator(func: Callable[..., dict]) -> Callable[..., dict]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict:
            try:
                return func(*args, **kwargs)
            except AIError as exc:
                print(f"[AI ERROR] {func.__name__}: {exc}")
                return fallback_factory(exc)
            except Exception as exc:  # last line of defense
                print(f"[AI UNEXPECTED ERROR] {func.__name__}: {exc}")
                return fallback_factory(exc)
        return wrapper
    return decorator


# ==============================================================================
# SECTION 3: RESPONSE HELPERS  (was: ai/utils/ai_response.py + prompt_loader.py)
# ==============================================================================

def success_response(data: dict) -> dict:
    """Wraps `data` with a success flag; keys of `data` are merged in directly."""
    return {"success": True, **data}


def error_response(message: str, code: Optional[str] = None, **extra: Any) -> dict:
    """Builds a standard error response. `message` must never contain secret values."""
    response: dict = {"success": False, "error": message}
    if code:
        response["code"] = code
    response.update(extra)
    return response


def build_prompt(template: str, **kwargs: str) -> str:
    """Formats a prompt template string with the given keyword arguments."""
    return template.format(**kwargs)


def _parse_json_response(raw_text: str) -> dict:
    """Strips ```json fences (if present) and parses Gemini's text as JSON."""
    cleaned = raw_text.strip()
    for fence in ("```json", "```"):
        if cleaned.startswith(fence):
            cleaned = cleaned[len(fence):]
    cleaned = cleaned.strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ResponseParsingError("Could not parse Gemini's response as JSON.") from exc


# ==============================================================================
# SECTION 4: GEMINI CLIENT  (was: ai/config/gemini_config.py)
# ==============================================================================

GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
_client = None  # lazy singleton


def is_gemini_configured() -> bool:
    """Returns True if a Gemini API key is present in the environment."""
    return bool(GEMINI_API_KEY)


def get_gemini_client():
    """
    Lazily creates and returns a singleton google-genai Client.

    Raises:
        AIConfigurationError: if GEMINI_API_KEY is not set.
    """
    global _client
    if not is_gemini_configured():
        raise AIConfigurationError("GEMINI_API_KEY is not set in the environment.")
    if _client is None:
        from google import genai  # imported lazily so this file still
        _client = genai.Client(api_key=GEMINI_API_KEY)  # loads without the package installed
    return _client


# ==============================================================================
# SECTION 5: EMERGENCY RESPONSE  (was: ai/emergency/*.py)
# ==============================================================================

SAFETY_INSTRUCTIONS: dict[str, list[str]] = {
    "fire": [
        "Move away from the fire.",
        "Use the nearest safe exit.",
        "Avoid elevators.",
        "Follow official evacuation instructions.",
    ],
    "earthquake": [
        "Drop, cover, and hold on.",
        "Stay away from windows.",
        "Avoid unstable objects.",
    ],
    "medical": [
        "Contact campus medical assistance.",
        "Keep the area clear.",
        "Provide first aid only if trained.",
    ],
    "flood": [
        "Move toward higher ground.",
        "Avoid flowing water.",
        "Follow official evacuation instructions.",
    ],
    "chemical": [
        "Move away from the affected area.",
        "Avoid direct contact.",
        "Follow campus safety instructions.",
    ],
    "crowd": [
        "Move calmly toward a safe area.",
        "Avoid pushing.",
        "Follow official instructions.",
    ],
    "unknown": [
        "Stay calm and move to a safe area.",
        "Keep your phone charged and share your location with a trusted person.",
        "Do not enter damaged buildings or touch fallen electrical wires.",
        "Use the SOS button to alert campus security.",
        "Follow instructions from campus staff.",
    ],
}


def normalize_emergency_type(emergency_type: str) -> str:
    """Ensures the emergency type is one of the supported categories."""
    normalized = (emergency_type or "").strip().lower()
    return normalized if normalized in EMERGENCY_TYPES else "unknown"


def get_instructions_for(emergency_type: str) -> list[str]:
    """Returns safety instructions for a type, falling back to 'unknown'."""
    normalized = normalize_emergency_type(emergency_type)
    return list(SAFETY_INSTRUCTIONS.get(normalized, SAFETY_INSTRUCTIONS["unknown"]))


def generate_emergency_response(emergency_type: str, severity: str = "medium") -> dict:
    """
    PUBLIC FUNCTION — returns structured, pre-reviewed safety instructions
    for a given emergency type. Does NOT call Gemini — instructions must
    stay reliable even if the AI provider is unavailable.

    Args:
        emergency_type: fire / earthquake / medical / flood / chemical /
            crowd, or anything else (normalized to 'unknown').
        severity: informational only, echoed back in the response.

    Returns:
        {"success": True, "emergency_type": str, "severity": str,
         "instructions": list[str]}
    """
    normalized_type = normalize_emergency_type(emergency_type)
    instructions = get_instructions_for(normalized_type)
    return success_response({
        "emergency_type": normalized_type,
        "severity": severity,
        "instructions": instructions,
    })


# ==============================================================================
# SECTION 6: RISK PREDICTION  (was: ai/prediction/*.py)
# ==============================================================================

RISK_WEIGHTS: dict[str, int] = {
    "fire": 35,
    "smoke": 20,
    "injury": 20,
    "chemical": 30,
    "crowd": 10,
    "blocked_exit": 15,
    "flood": 25,
}
MAX_SCORE: int = 100
CROWD_SIZE_THRESHOLD: int = 50
CROWD_SIZE_BONUS: int = 10
HIGH_RISK_LOCATIONS: set[str] = {"lab", "laboratory", "kitchen", "chemistry lab", "workshop"}
LOCATION_RISK_BONUS: int = 10


def classify_severity(score: int) -> str:
    """Maps a 0-100 risk score to low / medium / high / critical."""
    if not isinstance(score, (int, float)):
        raise InvalidInputError("Risk score must be a number.")
    if score < 0 or score > 100:
        raise InvalidInputError("Risk score must be between 0 and 100.")
    if score <= 29:
        return "low"
    if score <= 59:
        return "medium"
    if score <= 79:
        return "high"
    return "critical"


def _analyze_risk_factors(input_data: dict) -> tuple[int, list[str]]:
    """Applies RISK_WEIGHTS + contextual bonuses to input_data, capped at 100."""
    if not isinstance(input_data, dict):
        raise InvalidInputError("Prediction input must be a dictionary of factors.")

    score = 0
    factors: list[str] = []

    for factor, weight in RISK_WEIGHTS.items():
        if input_data.get(factor):
            score += weight
            factors.append(factor)

    num_people = input_data.get("number_of_people", 0)
    if isinstance(num_people, (int, float)) and num_people > CROWD_SIZE_THRESHOLD:
        score += CROWD_SIZE_BONUS
        factors.append("large_crowd")

    location = str(input_data.get("location_risk", "")).strip().lower()
    if location in HIGH_RISK_LOCATIONS:
        score += LOCATION_RISK_BONUS
        factors.append("high_risk_location")

    return min(score, MAX_SCORE), factors


@safe_ai_call(fallback_factory=lambda exc: error_response(
    "Could not calculate risk right now.", code="prediction_failed",
))
def predict_risk(input_data: dict) -> dict:
    """
    PUBLIC FUNCTION — calculates a rule-based emergency risk score (0-100).
    Fully rule-based, no Gemini call — deterministic and always available.

    Args:
        input_data: dict of boolean/contextual factors, e.g.
            {"fire": True, "smoke": True, "number_of_people": 80,
             "location_risk": "lab"}

    Returns:
        {"success": True, "risk_score": int, "severity": str, "factors": list[str]}
    """
    score, factors = _analyze_risk_factors(input_data)
    severity = classify_severity(score)
    return success_response({"risk_score": score, "severity": severity, "factors": factors})


# ==============================================================================
# SECTION 7: FAKE ALERT DETECTION  (was: ai/fake_alert/*.py)
# ==============================================================================

VERIFIED_THRESHOLD = 70
NEEDS_VERIFICATION_THRESHOLD = 40
_CHECK_WEIGHT = 25  # 4 checks x 25 = 100 max


def _check_required_fields(alert_data: dict) -> tuple[bool, Optional[str]]:
    required = ["description", "location"]
    missing = [f for f in required if not alert_data.get(f)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None


def _check_location(alert_data: dict) -> tuple[bool, Optional[str]]:
    location = str(alert_data.get("location", "")).strip()
    if not location:
        return False, "Location information is missing"
    if len(location) < 3:
        return False, "Location information is incomplete"
    return True, None


def _check_description(alert_data: dict) -> tuple[bool, Optional[str]]:
    description = str(alert_data.get("description", "")).strip()
    if len(description) < 10:
        return False, "Alert lacks supporting details"
    return True, None


def _check_repeated_reports(
    alert_data: dict, recent_reports: Optional[list[dict]] = None
) -> tuple[bool, Optional[str]]:
    """Does not penalize when no comparison data is available."""
    if not recent_reports:
        return True, None
    location = str(alert_data.get("location", "")).strip().lower()
    matching = [r for r in recent_reports if str(r.get("location", "")).strip().lower() == location]
    if len(matching) >= 2:
        return True, "Multiple independent reports from the same location"
    return True, None


def classify_alert_status(score: int) -> str:
    """Maps a 0-100 credibility score to verified / needs_verification / suspicious."""
    if score >= VERIFIED_THRESHOLD:
        return "verified"
    if score >= NEEDS_VERIFICATION_THRESHOLD:
        return "needs_verification"
    return "suspicious"


@safe_ai_call(fallback_factory=lambda exc: error_response(
    "Could not verify this alert right now.", code="verification_failed",
))
def detect_fake_alert(alert_data: dict, recent_reports: Optional[list[dict]] = None) -> dict:
    """
    PUBLIC FUNCTION — assesses an emergency alert's credibility using
    rule-based checks. NEVER declares an alert definitively fake — only
    classifies it so a human can prioritize what to check first.

    Args:
        alert_data: dict with at least 'description' and 'location'.
        recent_reports: optional list of other recent alerts, used to
            check for independent confirmation from the same area.

    Returns:
        {"success": True, "status": str, "score": int, "reasons": list[str]}
        status is one of: verified, needs_verification, suspicious.
    """
    if not isinstance(alert_data, dict):
        raise InvalidInputError("Alert data must be a dictionary.")

    score = 0
    reasons: list[str] = []
    checks = [
        _check_required_fields(alert_data),
        _check_location(alert_data),
        _check_description(alert_data),
        _check_repeated_reports(alert_data, recent_reports),
    ]
    for passed, reason in checks:
        if passed:
            score += _CHECK_WEIGHT
        elif reason:
            reasons.append(reason)

    status = classify_alert_status(score)
    if not reasons:
        reasons = ["No issues detected with the submitted alert."]

    return success_response({"status": status, "score": score, "reasons": reasons})


# ==============================================================================
# SECTION 8: CHATBOT  (was: ai/chatbot/*.py)
# ==============================================================================

GENERAL_SYSTEM_PROMPT = """You are a campus safety assistant for a Smart
Campus Emergency Response System. Identify the most likely emergency
category for the user's message and respond with safety-focused guidance.

Message: {message}

Respond ONLY with JSON in this exact format:
{{
  "emergency_type": "fire" or "earthquake" or "medical" or "flood" or "chemical" or "crowd" or "unknown",
  "severity": "low" or "medium" or "high" or "critical",
  "message": "one short reassuring sentence",
  "instructions": ["short instruction 1", "short instruction 2", "short instruction 3"]
}}"""

EMERGENCY_KEYWORDS: dict[str, list[str]] = {
    "fire": ["fire", "smoke", "burning", "flames"],
    "earthquake": ["earthquake", "tremor", "shaking", "quake"],
    "medical": ["injured", "injury", "bleeding", "unconscious", "medical", "heart attack", "pain"],
    "flood": ["flood", "flooding", "water rising", "waterlogged"],
    "chemical": ["gas leak", "chemical", "toxic", "fumes", "spill"],
    "crowd": ["stampede", "crowd", "crushed", "overcrowd"],
}

EMERGENCY_PROMPT_TEMPLATE = """You are an emergency assistant. The user's
message has been classified as a possible '{category}' emergency.

Message: {message}

Respond ONLY with JSON in this exact format:
{{
  "emergency_type": "{category}",
  "severity": "low" or "medium" or "high" or "critical",
  "message": "one short reassuring sentence",
  "instructions": ["short instruction 1", "short instruction 2", "short instruction 3"]
}}"""


def classify_emergency_type(message: str) -> str:
    """Deterministic keyword classifier, used before (or instead of) Gemini."""
    lowered = (message or "").lower()
    for category, keywords in EMERGENCY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "unknown"


def _build_emergency_prompt(message: str, category: str) -> str:
    normalized = category if category in EMERGENCY_TYPES else "unknown"
    return EMERGENCY_PROMPT_TEMPLATE.format(message=message, category=normalized)


def _normalize_severity(value: Optional[str]) -> str:
    normalized = (value or "").strip().lower()
    return normalized if normalized in SEVERITY_LEVELS else "medium"


def _format_chatbot_response(raw: dict, fallback_instructions: list[str]) -> dict:
    """Normalizes raw Gemini JSON into the stable chatbot response schema."""
    instructions = raw.get("instructions")
    if not isinstance(instructions, list) or not instructions:
        instructions = fallback_instructions

    message = str(raw.get("message") or "").strip()
    if not message:
        message = "Please follow the safety instructions below and stay calm."

    return {
        "success": True,
        "emergency_type": normalize_emergency_type(raw.get("emergency_type")),
        "severity": _normalize_severity(raw.get("severity")),
        "message": message,
        "instructions": instructions[:5],
    }


def _call_gemini_text(prompt: str) -> str:
    try:
        client = get_gemini_client()
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as exc:
        raise GeminiUnavailableError(f"Gemini call failed: {exc}") from exc


def _chatbot_fallback(message: str) -> dict:
    """Used when Gemini is unavailable/unconfigured — keyword classification
    plus predefined safety instructions, so the chatbot never goes silent."""
    category = classify_emergency_type(message)
    instructions = get_instructions_for(category)
    severity = "medium" if category != "unknown" else "low"
    return {
        "success": True,
        "emergency_type": category,
        "severity": severity,
        "message": "Here is guidance based on your message. If this is a real emergency, use the SOS button.",
        "instructions": instructions,
    }


@safe_ai_call(fallback_factory=lambda exc: error_response(
    "Could not process your message right now.", code="chatbot_failed",
))
def process_message(message: str) -> dict:
    """
    PUBLIC FUNCTION — AI Emergency Assistant. Classifies a user's message
    into an emergency category and returns structured safety guidance.

    Does NOT claim that emergency services were contacted — that is a
    separate backend action, not something this function performs.

    Args:
        message: free-text message from the user.

    Returns:
        {"success": bool, "emergency_type": str, "severity": str,
         "message": str, "instructions": list[str]}
    """
    if not message or not message.strip():
        return _chatbot_fallback("")

    if not is_gemini_configured():
        return _chatbot_fallback(message)

    category = classify_emergency_type(message)
    prompt = _build_emergency_prompt(message, category)
    raw_text = _call_gemini_text(prompt)
    parsed = _parse_json_response(raw_text)

    fallback_instructions = get_instructions_for(category)
    return _format_chatbot_response(parsed, fallback_instructions)


# ==============================================================================
# SECTION 9: VISION / IMAGE ANALYSIS  (was: ai/vision/*.py)
# ==============================================================================

IMAGE_ANALYSIS_PROMPT = """You are analyzing a photo submitted during a
possible campus emergency. Look for signs of: fire, smoke, injury, crowd,
blocked exits, flooding, or other hazardous conditions.

Do not claim certainty. Use cautious language such as "possible fire
detected" rather than definitive statements.

Respond ONLY with JSON in this exact format:
{
  "detected": true or false,
  "objects": ["fire", "smoke"],
  "severity": "low" or "medium" or "high" or "critical",
  "confidence": a number between 0 and 1,
  "description": "one short cautious sentence describing what you see"
}"""

_HIGH_SEVERITY_OBJECTS = {"fire", "chemical", "hazardous_condition"}
_MEDIUM_SEVERITY_OBJECTS = {"smoke", "injury", "flood", "blocked_exit"}


class DetectionResult(BaseModel):
    """Typed model representing an image analysis result."""
    detected: bool = False
    objects: list[str] = Field(default_factory=list)
    severity: str = "low"
    confidence: float = 0.0
    description: str = ""

    @field_validator("severity")
    @classmethod
    def _validate_severity(cls, value: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        normalized = (value or "").strip().lower()
        return normalized if normalized in allowed else "low"

    @field_validator("confidence")
    @classmethod
    def _validate_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, round(float(value), 2)))


def _validate_image_path(image_path: str) -> None:
    if not image_path or not isinstance(image_path, str):
        raise ImageProcessingError("Image path must be a non-empty string.")
    if not os.path.isfile(image_path):
        raise ImageProcessingError("Image file does not exist.")

    extension = image_path.rsplit(".", 1)[-1].lower() if "." in image_path else ""
    if extension not in SUPPORTED_IMAGE_TYPES:
        raise ImageProcessingError(
            f"Unsupported image type '.{extension}'. Allowed: {sorted(SUPPORTED_IMAGE_TYPES)}"
        )

    size_mb = os.path.getsize(image_path) / (1024 * 1024)
    if size_mb > MAX_IMAGE_SIZE_MB:
        raise ImageProcessingError(
            f"Image is too large ({size_mb:.1f}MB). Max allowed is {MAX_IMAGE_SIZE_MB}MB."
        )


def load_image(image_path: str) -> Image.Image:
    """Validates and safely opens an image file."""
    _validate_image_path(image_path)
    try:
        return Image.open(image_path)
    except UnidentifiedImageError as exc:
        raise ImageProcessingError("File could not be identified as a valid image.") from exc
    except Exception as exc:
        raise ImageProcessingError(f"Failed to open image: {exc}") from exc


def _estimate_severity(objects: list[str]) -> str:
    object_set = set(objects)
    if object_set & _HIGH_SEVERITY_OBJECTS:
        return "high"
    if object_set & _MEDIUM_SEVERITY_OBJECTS:
        return "medium"
    return "low"


def _call_gemini_vision(image) -> str:
    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=VISION_MODEL_NAME, contents=[IMAGE_ANALYSIS_PROMPT, image],
        )
        return response.text
    except Exception as exc:
        raise GeminiUnavailableError(f"Gemini vision call failed: {exc}") from exc


@safe_ai_call(fallback_factory=lambda exc: error_response(
    "Could not analyze this image right now.", code="vision_failed",
))
def analyze_image(image_path: str) -> dict:
    """
    PUBLIC FUNCTION — analyzes an image for possible emergency indicators
    (fire, smoke, injury, crowd, blocked exits, flooding, hazards).
    Never claims absolute certainty.

    Args:
        image_path: local filesystem path to a jpg/jpeg/png/webp image.

    Returns:
        {"success": bool, "detected": bool, "objects": list[str],
         "severity": str, "confidence": float, "description": str}
    """
    image = load_image(image_path)

    if not is_gemini_configured():
        result = DetectionResult(
            detected=False, objects=[], severity="low", confidence=0.0,
            description="AI image analysis is not configured; no automatic detection was performed.",
        )
        return success_response(result.model_dump())

    raw_text = _call_gemini_vision(image)
    parsed = _parse_json_response(raw_text)

    objects = parsed.get("objects") if isinstance(parsed.get("objects"), list) else []
    result = DetectionResult(
        detected=bool(parsed.get("detected", bool(objects))),
        objects=objects,
        severity=parsed.get("severity") or _estimate_severity(objects),
        confidence=parsed.get("confidence", 0.0),
        description=parsed.get("description", "Analysis completed."),
    )
    return success_response(result.model_dump())


# ==============================================================================
# SECTION 10: QUICK SELF-TEST (only runs if you execute this file directly)
# ==============================================================================

if __name__ == "__main__":
    print("Chatbot:", process_message("There is a fire near the hostel!"))
    print("Prediction:", predict_risk({"fire": True, "smoke": True}))
    print("Fake alert:", detect_fake_alert({"description": "Smoke near Block A entrance", "location": "Block A"}))
    print("Emergency:", generate_emergency_response("fire", "high"))
    print("\nGEMINI_API_KEY configured:", is_gemini_configured())
    print("If False above, chatbot/vision are using safe fallbacks — this is expected without a .env file.")