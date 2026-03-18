from google import genai
from google.genai import types
from dotenv import load_dotenv
import os, json, re

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_persona_action(prompt: str) -> dict:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=500,
                temperature=0.9,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        text = response.text.strip()
        text = re.sub(r'`json|`', '', text).strip()
        data = json.loads(text)

        if data.get("action") not in ["tweet", "reply", "quote", "nothing"]:
            data["action"] = "nothing"
        if len(data.get("content", "")) > 280:
            data["content"] = data["content"][:280]

        return data
    except Exception as e:
        print(f"Gemini error: {e}")
        return {"action": "nothing", "target_post_id": None, "content": None}
