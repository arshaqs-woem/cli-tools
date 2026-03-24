import os
from dotenv import load_dotenv

load_dotenv()

PLIVO_AUTH_ID = os.getenv("PLIVO_AUTH_ID")
PLIVO_AUTH_TOKEN = os.getenv("PLIVO_AUTH_TOKEN")


def validate_credentials():
    if not PLIVO_AUTH_ID or not PLIVO_AUTH_TOKEN:
        raise ValueError("Missing PLIVO_AUTH_ID or PLIVO_AUTH_TOKEN in .env file.")
