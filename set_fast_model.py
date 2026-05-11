import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

try:
    data = requests.get('https://openrouter.ai/api/v1/models').json()['data']
    free_models = [m['id'] for m in data if m.get('pricing', {}).get('prompt', '0') == '0' and 'free' in m['id'].lower()]

    fast_models = [m for m in free_models if 'flash' in m.lower() or '8b' in m.lower() or '7b' in m.lower() or 'mini' in m.lower()]
    fast_models += [m for m in free_models if m not in fast_models and 'nemotron' not in m.lower()]

    success = None
    for model in fast_models:
        print(f"Testing speed on {model}...")
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5},
                timeout=5
            )
            if response.status_code == 200:
                print(f"SUCCESS: {model}")
                success = model
                break
        except Exception as e:
            pass

    if success:
        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("LLM_MODEL="):
                    f.write(f"LLM_MODEL={success}\n")
                else:
                    f.write(line)
        print(f"\n=> Optimized .env to use {success}")
except Exception as e:
    print(e)
