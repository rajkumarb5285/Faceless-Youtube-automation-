import os
import sys
import base64
import httpx
from dotenv import load_dotenv

# Step 3: Load credentials strictly from environment without printing
load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

if not SARVAM_API_KEY:
    raise ValueError("SARVAM_API_KEY not found in environment (.env).")

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Test parameters for Sarvam AI Bulbul v3
text_input = "नमस्ते! यह सरवम एआई का पहला ऑडियो टेस्ट है, जो हमारे फेसलेस यूट्यूब स्टूडियो के लिए तैयार किया गया है।"
language_code = "hi-IN"
speaker = "priya"
model = "bulbul:v3"
output_file = "sarvam_test_output.wav"

print("--- Calling Sarvam AI Text-to-Speech API ---")
print(f"Endpoint: https://api.sarvam.ai/text-to-speech")
print(f"Model: {model}")
print(f"Speaker: {speaker}")
print(f"Language: {language_code}")
print(f"Script: Devanagari (Hindi)")

# Make HTTP call to Sarvam AI API
headers = {
    "api-subscription-key": SARVAM_API_KEY,
    "Content-Type": "application/json"
}
payload = {
    "inputs": [text_input],
    "target_language_code": language_code,
    "speaker": speaker,
    "model": model,
    "enable_preprocessing": True
}

resp = httpx.post("https://api.sarvam.ai/text-to-speech", json=payload, headers=headers, timeout=30.0)
resp.raise_for_status()

data = resp.json()
audio_base64 = data["audios"][0]
audio_bytes = base64.b64decode(audio_base64)

# Save audio to disk
with open(output_file, "wb") as f:
    f.write(audio_bytes)

print(f"\n[SUCCESS] 200 OK received from Sarvam AI!")
print(f"[OUTPUT] Audio successfully saved to: {os.path.abspath(output_file)}")
print(f"[STATS] Audio size: {len(audio_bytes) / 1024:.2f} KB ({len(audio_bytes)} bytes)")
