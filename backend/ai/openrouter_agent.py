import requests
from dotenv import load_dotenv
import os, json, re

load_dotenv()

def get_persona_action_openrouter(prompt: str) -> dict:
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "AITTER"
            },
            json={
                "model": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 1.3,
            }
        )
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        text = re.sub(r'`json|`', '', text).strip()
        result = json.loads(text)

        if result.get("action") not in ["tweet", "reply", "quote", "nothing"]:
            result["action"] = "nothing"
        if len(result.get("content", "")) > 280:
            result["content"] = result["content"][:280]

        return result
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return {"action": "nothing", "target_post_id": None, "content": None}
