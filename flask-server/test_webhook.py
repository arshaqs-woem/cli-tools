import requests

url = "https://unstumbling-donovan-nonadvantageously.ngrok-free.dev/webhook-test"

data = {"caller": "+1234567890", "event": "incoming_call"}

response = requests.post(url, json=data, verify=False)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
