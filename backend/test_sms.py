import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# .env file load karein
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

# SMS Gateway Config
SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "https://api.sms-gate.app/3rdparty/v1/message")
SMS_GATEWAY_USERNAME = os.getenv("SMS_GATEWAY_USERNAME", "-FVLMS")
SMS_GATEWAY_PASSWORD = os.getenv("SMS_GATEWAY_PASSWORD", "-itocm7jdwizxm")
SMS_GATEWAY_DEVICE_ID = os.getenv("SMS_GATEWAY_DEVICE_ID", "dgQAJSHkZJ9OWQCtjvsJi")

def send_test_sms(phone_number: str, message: str):
    clean_phone = "".join([c for c in str(phone_number) if c.isdigit() or c == '+'])

    # API array/list format expect karta hai: "phoneNumbers": [...]
    payload = {
        "phoneNumbers": [clean_phone],
        "message": message
    }

    print(f"📡 Sending SMS to: {clean_phone}")
    print(f"🔗 Gateway URL: {SMS_GATEWAY_URL}")
    print(f"👤 Username: {SMS_GATEWAY_USERNAME}\n")

    try:
        response = requests.post(
            SMS_GATEWAY_URL,
            auth=(SMS_GATEWAY_USERNAME, SMS_GATEWAY_PASSWORD),
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        print("HTTP Status Code:", response.status_code)
        print("Response Body:", response.text)

        if response.status_code in [200, 201, 202]:
            print("\n✅ SUCCESS: Message gateway tak pahuch gaya! Phone check karein.")
        else:
            print("\n❌ FAILED: Gateway ne reject kiya. Details upar response me dekhein.")
    except Exception as e:
        print("\n❌ EXCEPTION:", str(e))

if __name__ == "__main__":
    # Yahan apna 10 digit ka actual mobile number daalein (+91 ke baad apna number)
    MY_PHONE_NUMBER = "+916393645985"

    send_test_sms(MY_PHONE_NUMBER, "🚨 Smart Campus Test: Emergency SMS Gateway working!")
