import requests
import json

url = "http://localhost:5000/notifications"
payload = {
    "topic": "questions",
    "resource": "/questions/12345",
    "user_id": 71527835,
    "application_id": 4601797779457193,
    "sent": "2025-11-30T10:00:00.000Z"
}

print(f"Enviando POST para {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"\nErro ao conectar: {e}")
