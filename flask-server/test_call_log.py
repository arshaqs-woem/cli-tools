import requests

BASE = "http://localhost:5000"

fake_calls = [
    {"caller_number": "+14155551234", "called_number": "+912264237030", "call_status": "completed"},
    {"caller_number": "+14155555678", "called_number": "+912264237030", "call_status": "failed"},
    {"caller_number": "+14155559999", "called_number": "+912264237030", "call_status": "completed"},
]

for call in fake_calls:
    response = requests.post(f"{BASE}/log-call", json=call)
    print(f"Logged: {call['caller_number']} → {response.json()}")

print("\nAll call logs:")
response = requests.get(f"{BASE}/call-logs")
for log in response.json():
    print(f"  [{log['id']}] {log['caller_number']} | {log['call_status']} | {log['created_at']}")
