import sys
import requests
from config import validate_credentials
from api import get_account_balance, get_message_logs


def print_report(balance, sent_today, failed):
    print("=" * 45)
    print("       PLIVO ACCOUNT HEALTH REPORT")
    print("=" * 45)
    print(f"  Account Balance:      ${balance:.2f}")
    print(f"  Messages Sent Today:  {len(sent_today)}")
    print(f"  Failed Messages:      {len(failed)}")

    if failed:
        print("\n  Failed Message Details:")
        for msg in failed:
            number = getattr(msg, "to_number", "unknown")
            state = getattr(msg, "message_state", "unknown")
            time = getattr(msg, "message_time", "unknown")
            print(f"    - To: {number} | Status: {state} | Time: {time}")
    else:
        print("\n  No failed messages today.")

    if balance < 5.00:
        print(f"\n  WARNING: Low balance (${balance:.2f}). Top up soon.")

    print("=" * 45)


def main():
    try:
        validate_credentials()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    try:
        print("Fetching account data from Plivo...")
        balance = get_account_balance()
        sent_today, failed = get_message_logs()
        print_report(balance, sent_today, failed)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Authentication error: Invalid Plivo credentials. Check your .env file.")
        else:
            print(f"API error: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Network error: Could not reach Plivo API. Check your internet connection.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Timeout error: Plivo API took too long to respond.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
