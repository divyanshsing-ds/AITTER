import sys
sys.path.append('.')
from core.database import SessionLocal
from models.persona import AIPersona
from ai.prompt_builder import build_system_prompt
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

db = SessionLocal()
persona = db.query(AIPersona).filter(AIPersona.name == "DesiBro_AI").first()
prompt = build_system_prompt(persona)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        max_output_tokens=500,
        temperature=0.9,
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )
)
print("RAW RESPONSE:")
print(response.text)
db.close()
