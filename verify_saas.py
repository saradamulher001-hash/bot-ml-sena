import requests
import sqlite3
import os

# 1. Verify DB creation
if os.path.exists('users.db'):
    print("SUCCESS: users.db created.")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        print("SUCCESS: users table exists.")
    else:
        print("FAILURE: users table missing.")
    conn.close()
else:
    print("FAILURE: users.db not found.")

# 2. Mock /callback (Simulate saving a user)
# We can't easily mock the full OAuth flow without a browser, but we can manually insert a user into the DB to test notifications
print("\nManually inserting test user into DB...")
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
test_user_id = "123456789"
test_token = os.getenv('MERCADO_LIVRE_TOKEN') # Use the real token from env for testing
cursor.execute("INSERT OR REPLACE INTO users (user_id, access_token, refresh_token) VALUES (?, ?, ?)", (test_user_id, test_token, "refresh_dummy"))
conn.commit()
conn.close()
print(f"Inserted User {test_user_id} with token.")

# 3. Test /notifications with this user_id
print("\nTesting /notifications for SaaS user...")
payload = {
    "topic": "questions",
    "resource": "/questions/123", # This will fail to fetch if not mocked, but we check if it TRIES to fetch
    "user_id": test_user_id,
    "_id": "notif123"
}

# We need to mock the ML API calls inside app.py or just see if it hits the logic
# Since we are running against the real app.py, we can't easily mock internal requests without patching app.py or using a complex setup.
# However, we can check if the app accepts the request and logs the correct flow.
# We will rely on the server logs for detailed verification, but here we expect a 200 OK.

try:
    response = requests.post("http://localhost:5000/notifications", json=payload)
    print(f"Notification Response: {response.status_code} {response.json()}")
    if response.status_code == 200:
        print("SUCCESS: Notification endpoint accepted request.")
    else:
        print("FAILURE: Notification endpoint returned error.")
except Exception as e:
    print(f"FAILURE: Could not hit endpoint: {e}")
