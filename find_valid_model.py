import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

try:
    data = requests.get('https://openrouter.ai/api/v1/models').json()['data']
    free_models = [m['id'] for m in data if m.get('pricing', {}).get('prompt', '0') == '0' and 'free' in m['id'].lower()]
    
    print(f"Found {len(free_models)} free models.")
    
    success = None
    for model in free_models:
        print(f"Testing {model}...")
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hi"}]
                }
            )
            if response.status_code == 200:
                print(f"SUCCESS: {model}")
                success = model
                break
            else:
                print(f"FAILED {model}: {response.status_code}")
        except Exception as e:
            print(f"ERROR {model}: {e}")

    if success:
        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("LLM_MODEL="):
                    f.write(f"LLM_MODEL={success}\n")
                else:
                    f.write(line)
        print(f"Wrote {success} to .env!")
except Exception as e:
    print(e)
