import requests

response = requests.get("https://openrouter.ai/api/v1/models")
models = response.json().get("data", [])
free_models = [m["id"] for m in models if "free" in m["id"].lower()]
print("Free models:", free_models[:20])
