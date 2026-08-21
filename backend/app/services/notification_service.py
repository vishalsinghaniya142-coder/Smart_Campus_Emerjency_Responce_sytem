import os
import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# --- General Notification Settings ---
NOTIFICATION_ENABLED = os.getenv("NOTIFICATION_ENABLED", "true").lower() == "true"
SMS_ENABLED = os.getenv("SMS_ENABLED", "true").lower() == "true"
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"

# --- SMS Gateway Settings ---
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
    """Phone number se extra symbols remove karta hai."""
    if not phone:
        return ""
    return "".join([c for c in str(phone) if c.isdigit() or c == '+'])

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


def send_sms_to_active_contacts(contacts: List[Any], message: str) -> Dict[str, Any]:
    """
    Sirf active/activated contacts filter karta hai aur first 10 numbers ko SMS bhejta hai.
    """
    if not contacts:
        return {"status": "skipped", "reason": "no_contacts", "sent_count": 0}

    # 1. Filter only active contacts
    active_contacts = []
    for c in contacts:
        if isinstance(c, dict):
            is_act = c.get("is_active", False) or c.get("activated", False) or c.get("status") == "active"
        else:
            is_act = getattr(c, "is_active", False) or getattr(c, "activated", False) or getattr(c, "status", "") == "active"

        if is_act:
            active_contacts.append(c)

    # 2. Limit to maximum 10 active numbers
    selected_targets = active_contacts[:SMS_ALERT_LIMIT]

    sent_count = 0
    failed_count = 0
    delivered_numbers = []

    for contact in selected_targets:
        if isinstance(contact, dict):
            phone = contact.get("phone") or contact.get("phone_number") or contact.get("mobile")
        else:
            phone = getattr(contact, "phone", None) or getattr(contact, "phone_number", None) or getattr(contact, "mobile", None)

        if not phone:
            continue

        success = send_sms_via_gateway(phone, message)
        if success:
            sent_count += 1
            delivered_numbers.append(phone)
        else:
            failed_count += 1

    return {
        "status": "completed",
        "total_active_found": len(active_contacts),
        "targeted_limit": SMS_ALERT_LIMIT,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "delivered_to": delivered_numbers
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

    # SMS Dispatch to Active 10
    sms_summary = {}
    if contacts and SMS_ENABLED:
        sms_summary = send_sms_to_active_contacts(contacts, full_message)

    telegram_status = False
    if TELEGRAM_ENABLED:
        telegram_status = NotificationService.send_telegram(full_message)

    return {
        "status": "success",
        "alert_title": alert_title,
        "sms_dispatch": sms_summary,
        "telegram_sent": telegram_status
    }
