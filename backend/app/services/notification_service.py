import os
import smtplib
import requests
import logging
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

from google.cloud.firestore_v1.base_query import FieldFilter

from app.services.database.firebase_client import db

logger = logging.getLogger(__name__)

# --- General Notification Settings ---
NOTIFICATION_ENABLED = os.getenv("NOTIFICATION_ENABLED", "true").lower() == "true"
SMS_ENABLED = os.getenv("SMS_ENABLED", "true").lower() == "true"
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"

# --- SMS Gateway Settings ---
SMS_GATEWAY_URL = os.getenv(
    "SMS_GATEWAY_URL",
    "https://api.sms-gate.app",
)

SMS_GATEWAY_USERNAME = os.getenv(
    "SMS_GATEWAY_USERNAME",
    "",
)

SMS_GATEWAY_PASSWORD = os.getenv(
    "SMS_GATEWAY_PASSWORD",
    "",
)

SMS_GATEWAY_DEVICE_ID = os.getenv(
    "SMS_GATEWAY_DEVICE_ID",
    "",
)

SMS_ALERT_LIMIT = int(
    os.getenv("SMS_ALERT_LIMIT", "10")
)
TEMPORARY_SMS_RECIPIENTS = os.getenv(
    "TEMPORARY_SMS_RECIPIENTS",
    "",
)

# --- Email Settings ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USERNAME)

# --- Telegram Settings ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# =========================================================
# HELPER FUNCTIONS: SMS GATEWAY & ACTIVE FILTER
# =========================================================

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to a gateway-safe value."""
    if not phone:
        return ""
    cleaned = "".join([c for c in str(phone) if c.isdigit() or c == '+'])
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    return cleaned


def get_active_users_with_phone_numbers() -> List[str]:
    """Return deduplicated active Firestore user phone numbers."""
    users = list(
        db.collection("users")
        .where(filter=FieldFilter("is_active", "==", True))
        .stream()
    )

    seen = set()
    phone_numbers: List[str] = []

    for document in users:
        data = document.to_dict() or {}
        phone_number = data.get("phone_number")
        if not phone_number:
            continue

        sanitized = normalize_phone_number(phone_number)
        if not sanitized or len(sanitized) < 10:
            continue

        if sanitized in seen:
            continue

        seen.add(sanitized)
        phone_numbers.append(sanitized)

    return phone_numbers


def get_configured_sms_recipients() -> List[str]:
    """Return server-configured emergency recipients."""
    recipients: List[str] = []
    seen = set()

    for value in TEMPORARY_SMS_RECIPIENTS.split(","):
        phone_number = normalize_phone_number(value)
        if phone_number and len(phone_number) >= 10 and phone_number not in seen:
            seen.add(phone_number)
            recipients.append(phone_number)

    return recipients


def get_emergency_sms_recipients() -> List[str]:
    """Combine active users with server-configured emergency recipients."""
    recipients = get_active_users_with_phone_numbers()
    seen = set(recipients)

    for phone_number in get_configured_sms_recipients():
        if phone_number not in seen:
            seen.add(phone_number)
            recipients.append(phone_number)

    return recipients


def build_sms_contacts(phone_numbers: List[str]) -> List[Dict[str, Any]]:
    return [
        {"phone_number": phone_number, "is_active": True}
        for phone_number in phone_numbers
    ]


def make_google_maps_url(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps?q={latitude},{longitude}"


def send_sms_via_gateway(phone_number: str, message: str) -> bool:
    """Send one SMS through SMS-Gate using JWT authentication."""

    if not SMS_ENABLED:
        logger.info("SMS dispatch skipped: SMS_ENABLED is false.")
        return False

    clean_phone = normalize_phone_number(phone_number)

    if not clean_phone:
        logger.warning("SMS skipped: empty phone number.")
        return False

    if not SMS_GATEWAY_USERNAME or not SMS_GATEWAY_PASSWORD:
        logger.error("SMS Gateway credentials are not configured.")
        return False

    token_url = (
        f"{SMS_GATEWAY_URL.rstrip('/')}"
        "/3rdparty/v1/auth/token"
    )

    messages_url = (
        f"{SMS_GATEWAY_URL.rstrip('/')}"
        "/3rdparty/v1/messages"
    )

    try:
        token_response = requests.post(
            token_url,
            auth=(
                SMS_GATEWAY_USERNAME,
                SMS_GATEWAY_PASSWORD,
            ),
            headers={
                "Content-Type": "application/json"
            },
            json={
                "ttl": 3600,
                "scopes": ["messages:send"],
            },
            timeout=15,
        )

        if token_response.status_code != 201:
            logger.error(
                f"SMS-Gate token request failed: "
                f"{token_response.status_code} "
                f"{token_response.text}"
            )
            return False

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            logger.error("SMS-Gate did not return an access token.")
            return False

        payload = {
            "phoneNumbers": [clean_phone],
            "textMessage": {
                "text": message
            },
        }

        if SMS_GATEWAY_DEVICE_ID:
            payload["deviceId"] = SMS_GATEWAY_DEVICE_ID

        response = requests.post(
            messages_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        if response.status_code in (200, 201, 202):
            logger.info(
                f"SMS successfully dispatched to {clean_phone}"
            )
            return True

        logger.error(
            f"SMS-Gate message request failed: "
            f"{response.status_code} {response.text}"
        )
        return False

    except requests.RequestException as exc:
        logger.error(f"SMS Gateway network error: {exc}")
        return False

    except Exception as exc:
        logger.error(f"Unexpected SMS error: {exc}")
        return False


def send_sms_to_active_contacts(
    contacts: List[Any],
    message: str,
    limit: Optional[int] = SMS_ALERT_LIMIT,
) -> Dict[str, Any]:
    """Deliver to active contacts while de-duping valid numbers."""
    if not contacts:
        return {"status": "skipped", "reason": "no_contacts", "sent_count": 0}

    active_contacts: List[Any] = []
    for contact in contacts:
        if isinstance(contact, dict):
            is_active = contact.get("is_active", False) or contact.get("activated", False) or contact.get("status") == "active"
        else:
            is_active = getattr(contact, "is_active", False) or getattr(contact, "activated", False) or getattr(contact, "status", "") == "active"

        if is_active:
            active_contacts.append(contact)

    selected_targets = active_contacts if limit is None else active_contacts[:limit]

    seen_phone_numbers = set()
    sent_count = 0
    failed_count = 0
    delivered_numbers: List[str] = []

    for contact in selected_targets:
        if isinstance(contact, dict):
            phone = contact.get("phone") or contact.get("phone_number") or contact.get("mobile")
        else:
            phone = getattr(contact, "phone", None) or getattr(contact, "phone_number", None) or getattr(contact, "mobile", None)

        if not phone:
            continue

        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone or len(normalized_phone) < 10:
            continue

        if normalized_phone in seen_phone_numbers:
            continue
        seen_phone_numbers.add(normalized_phone)

        success = send_sms_via_gateway(normalized_phone, message)
        if success:
            sent_count += 1
            delivered_numbers.append(normalized_phone)
        else:
            failed_count += 1

    return {
        "status": "completed",
        "total_active_found": len(active_contacts),
        "targeted_limit": limit,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "delivered_to": delivered_numbers,
    }


# =========================================================
# NOTIFICATION SERVICE CLASS
# =========================================================
class SmsGatewayNotificationService:
    """Adapter for sending SMS through SMS-Gate."""

    async def send_message(
        self,
        phone_number: str,
        message: str,
    ) -> Dict[str, Any]:

        success = send_sms_via_gateway(
            phone_number,
            message,
        )

        if success:
            return {
                "success": True,
                "phone_number": phone_number,
                "message": "SMS submitted successfully.",
            }

        return {
            "success": False,
            "phone_number": phone_number,
            "message": "SMS could not be sent.",
        }

    async def send_sos_notification(self, sos) -> Dict[str, Any]:
        """Broadcast an SOS to all active users and store an in-app record."""

        sender_name = "Unknown User"
        try:
            sender_document = db.collection("users").document(str(sos.user_id)).get()
            if sender_document.exists:
                sender_name = sender_document.to_dict().get("name") or sender_name
        except Exception as exc:
            logger.warning(f"Unable to load sender user for SOS notification: {exc}")

        latitude = getattr(getattr(sos, "location", {}), "latitude", None)
        longitude = getattr(getattr(sos, "location", {}), "longitude", None)
        if isinstance(sos.location, dict):
            latitude = sos.location.get("latitude")
            longitude = sos.location.get("longitude")

        if latitude is None or longitude is None:
            latitude = 0.0
            longitude = 0.0

        message = (
            "🚨 EMERGENCY SOS 🚨\n"
            f"Sender/User: {sender_name}\n"
            "Message: Emergency SOS has been triggered.\n\n"
            "Location:\n"
            f"Latitude: {latitude}\n"
            f"Longitude: {longitude}\n"
            f"Google Maps:\n{make_google_maps_url(float(latitude), float(longitude))}"
        )

        active_phone_numbers = get_emergency_sms_recipients()
        sms_result = send_sms_to_active_contacts(
            build_sms_contacts(active_phone_numbers),
            message,
            limit=None,
        )

        notification_id = f"sos_{uuid.uuid4().hex}"
        db.collection("notifications").document(notification_id).set({
            "type": "sos",
            "title": "Emergency SOS",
            "message": message,
            "sos_id": sos.id,
            "sender_id": sos.user_id,
            "created_at": getattr(sos, "created_at", None),
            "status": "active",
            "active_users_found": len(active_phone_numbers),
            "sms_sent": sms_result.get("sent_count", 0),
            "sms_failed": sms_result.get("failed_count", 0),
        })

        logger.info(
            "Emergency notification started | "
            f"Active users found: {len(active_phone_numbers)} | "
            f"SMS targets: {len(active_phone_numbers)} | "
            f"SMS sent: {sms_result.get('sent_count', 0)} | "
            f"SMS failed: {sms_result.get('failed_count', 0)}"
        )

        return {"sms": sms_result, "notification_id": notification_id}

    async def send_incident_notification(self, incident) -> Dict[str, Any]:
        """Broadcast a submitted incident to all active registered users."""
        location = getattr(incident, "location", None)
        latitude = getattr(location, "latitude", None) if location is not None else None
        longitude = getattr(location, "longitude", None) if location is not None else None
        if isinstance(location, dict):
            latitude = location.get("latitude")
            longitude = location.get("longitude")

        if latitude is None or longitude is None:
            latitude = 0.0
            longitude = 0.0

        location_text = getattr(location, "address", None) if location is not None else None
        if isinstance(location, dict):
            location_text = location.get("address") or ""

        incident_type = getattr(incident, "incident_type", None)
        if hasattr(incident_type, "value"):
            incident_type = incident_type.value

        severity = getattr(incident, "severity", None)
        if hasattr(severity, "value"):
            severity = severity.value

        message = (
            "🚨 EMERGENCY REPORT 🚨\n"
            f"Type:\n{incident_type}\n\n"
            f"Title:\n{incident.title}\n\n"
            f"Description:\n{incident.description}\n\n"
            f"Severity:\n{severity}\n\n"
            f"Location:\n{location_text or 'Not provided'}\n\n"
            f"GPS:\n{latitude}, {longitude}\n\n"
            f"Google Maps:\n{make_google_maps_url(float(latitude), float(longitude))}"
        )

        active_phone_numbers = get_emergency_sms_recipients()
        sms_result = send_sms_to_active_contacts(
            build_sms_contacts(active_phone_numbers),
            message,
            limit=None,
        )

        notification_id = f"incident_{uuid.uuid4().hex}"
        db.collection("notifications").document(notification_id).set({
            "type": "incident",
            "title": "Emergency Report",
            "message": message,
            "incident_id": incident.id,
            "created_at": getattr(incident, "created_at", None),
            "status": "active",
            "active_users_found": len(active_phone_numbers),
            "sms_sent": sms_result.get("sent_count", 0),
            "sms_failed": sms_result.get("failed_count", 0),
        })

        logger.info(
            "Emergency notification started | "
            f"Active users found: {len(active_phone_numbers)} | "
            f"SMS targets: {len(active_phone_numbers)} | "
            f"SMS sent: {sms_result.get('sent_count', 0)} | "
            f"SMS failed: {sms_result.get('failed_count', 0)}"
        )

        return {"sms": sms_result, "notification_id": notification_id}

    async def send_alert_notification(self, alert) -> Dict[str, Any]:
        """Send SMS for active alerts created intentionally for broadcast."""
        raw_status = getattr(alert, "status", "")
        status_value = getattr(raw_status, "value", raw_status)
        status_name = str(status_value).lower()
        if status_name != "active":
            logger.info(f"Alert SMS skipped because alert status is {status_name!r}.")
            return {"success": True, "alert_id": str(getattr(alert, "id", "")), "sms": {"status": "skipped"}}

        location = getattr(alert, "location", None)
        latitude = getattr(location, "latitude", None) if location is not None else None
        longitude = getattr(location, "longitude", None) if location is not None else None
        if isinstance(location, dict):
            latitude = location.get("latitude")
            longitude = location.get("longitude")

        location_text = "Not provided"
        if location is not None:
            location_text = getattr(location, "address", None) or ""
            if isinstance(location, dict):
                location_text = location.get("address") or "Not provided"

        alert_type = getattr(alert, "alert_type", None)
        if hasattr(alert_type, "value"):
            alert_type = alert_type.value

        alert_severity = getattr(alert, "severity", None)
        if hasattr(alert_severity, "value"):
            alert_severity = alert_severity.value

        maps_url = ""
        if latitude is not None and longitude is not None:
            maps_url = make_google_maps_url(float(latitude), float(longitude))

        message = (
            "🚨 EMERGENCY ALERT 🚨\n"
            f"Title:\n{alert.title}\n\n"
            f"Message:\n{alert.message}\n\n"
            f"Severity:\n{alert_severity}\n\n"
            f"Type:\n{alert_type}\n\n"
            f"Location:\n{location_text}\n"
        )
        if maps_url:
            message += f"\nGPS:\n{latitude}, {longitude}\n\nGoogle Maps:\n{maps_url}"

        active_phone_numbers = get_emergency_sms_recipients()
        sms_result = send_sms_to_active_contacts(
            build_sms_contacts(active_phone_numbers),
            message,
            limit=None,
        )

        notification_id = f"alert_{uuid.uuid4().hex}"
        db.collection("notifications").document(notification_id).set({
            "type": "alert",
            "title": alert.title,
            "message": message,
            "alert_id": alert.id,
            "status": "active",
            "active_users_found": len(active_phone_numbers),
            "sms_sent": sms_result.get("sent_count", 0),
            "sms_failed": sms_result.get("failed_count", 0),
        })

        logger.info(
            "Emergency notification started | "
            f"Active users found: {len(active_phone_numbers)} | "
            f"SMS targets: {len(active_phone_numbers)} | "
            f"SMS sent: {sms_result.get('sent_count', 0)} | "
            f"SMS failed: {sms_result.get('failed_count', 0)}"
        )

        return {"success": True, "alert_id": str(getattr(alert, "id", "")), "sms": sms_result}

    async def cancel_alert_notification(self, alert) -> Dict[str, Any]:
        """Alert cancellation does not require an external SMS operation."""

        return {"success": True, "alert_id": str(getattr(alert, "id", ""))}


class NotificationService:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:
        if not EMAIL_ENABLED or not SMTP_USERNAME or not SMTP_PASSWORD:
            return False
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_FROM
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False

    @staticmethod
    def send_telegram(message: str) -> bool:
        if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return False
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
            res = requests.post(url, json=payload, timeout=8)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Telegram alert failed: {str(e)}")
            return False

    @classmethod
    def send_sos_broadcast(
        cls,
        title: str,
        message: str,
        contacts: Optional[List[Any]] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return send_emergency_notification(title, message, contacts, location)


# =========================================================
# STANDALONE DISPATCHER FUNCTIONS
# =========================================================

def send_emergency_notification(
    alert_title: str,
    alert_message: str,
    contacts: Optional[List[Any]] = None,
    location_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if not NOTIFICATION_ENABLED:
        logger.info("Emergency notifications are globally disabled.")
        return {"status": "disabled"}

    full_message = f"🚨 {alert_title} 🚨\n{alert_message}"
    if location_details and location_details.get("maps_url"):
        full_message += f"\nLocation: {location_details.get('maps_url')}"

    sms_summary = {}
    if SMS_ENABLED:
        configured_contacts = build_sms_contacts(get_configured_sms_recipients())
        sms_contacts = configured_contacts + (contacts or [])
        sms_summary = send_sms_to_active_contacts(sms_contacts, full_message, limit=None)

    telegram_status = False
    if TELEGRAM_ENABLED:
        telegram_status = NotificationService.send_telegram(full_message)

    return {
        "status": "success",
        "alert_title": alert_title,
        "sms_dispatch": sms_summary,
        "telegram_sent": telegram_status,
    }
