import requests
import json

response = requests.get("https://openrouter.ai/api/v1/models")
if response.status_code == 200:
    data = response.json()
    free_models = []
    for model in data.get("data", []):
        pricing = model.get("pricing", {})
        if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
            free_models.append(model["id"])
    
    print("Found free models:")
    for m in free_models[:10]:
        print(f"- {m}")
else:
    print(f"Error {response.status_code}: {response.text}")
