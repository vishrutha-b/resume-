import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")
print(f"Loaded key: {key[:15]}...")

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {key}",
    },
    json={
        "model": "google/gemma-4-31b-it:free",
        "messages": [{"role": "user", "content": "Say OK in one word."}]
    }
)

if response.status_code == 200:
    print("SUCCESS! The API key is valid.")
else:
    print(f"FAILED! Status code: {response.status_code}")
    print(response.text)
