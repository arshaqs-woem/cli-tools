import requests
from datetime import datetime, timezone
from config import PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN

BASE_URL = "https://api.plivo.com/v1/Account"


def get_account_balance():
    url = f"{BASE_URL}/{PLIVO_AUTH_ID}/"
    response = requests.get(url, auth=(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN), timeout=10)
    response.raise_for_status()
    data = response.json()
    return float(data["cash_credits"])


def get_message_logs():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d 00:00:00")
    url = f"{BASE_URL}/{PLIVO_AUTH_ID}/Message/"
    params = {"message_time__gte": today, "limit": 20, "offset": 0}
    response = requests.get(url, auth=(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN), params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    messages = data.get("objects", [])
    failed = [m for m in messages if m.get("message_state") in ("failed", "undelivered")]

    return messages, failed
