from pyngrok import ngrok
import time

# 1. Open the Tunnel to port 8501 (where Streamlit runs)
# Note: If it asks for a token, sign up at ngrok.com and paste it below like:
# ngrok.set_auth_token("YOUR_TOKEN_HERE")

print("🔄 Connecting to the internet...")
try:
    public_url = ngrok.connect(8501).public_url
    print(f"\n✅ YOUR APP IS LIVE HERE: {public_url}\n")
    print("(Press Ctrl+C to stop)")
    
    # Keep the script running so the link stays alive
    while True:
        time.sleep(1)
except Exception as e:
    print(f"Error: {e}")
    print("Tip: You might need to create a free account on ngrok.com and add your token.")