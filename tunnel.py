from pyngrok import ngrok
import time

# Set auth token
ngrok.set_auth_token("36DHruWLEPPU08c9I8mC6rpoXtJ_2WZJjxUp4EiZVsRkAdbf7")

# Open a HTTP tunnel on port 5000
public_url = ngrok.connect(5000).public_url
print(f"Ngrok Tunnel URL: {public_url}")

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Closing tunnel...")
    ngrok.disconnect(public_url)
