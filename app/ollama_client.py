import requests

OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"

def query_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.RequestException as e:
        return f"Ollama API error: {str(e)}"
