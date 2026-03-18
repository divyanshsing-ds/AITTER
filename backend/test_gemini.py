import sys
sys.path.append('.')
from core.database import SessionLocal
from models.persona import AIPersona
from ai.prompt_builder import build_system_prompt
from ai.gemini_agent import get_persona_action

db = SessionLocal()
persona = db.query(AIPersona).filter(AIPersona.name == "DesiBro_AI").first()

prompt = build_system_prompt(persona)
result = get_persona_action(prompt)

print(f"Action: {result['action']}")
print(f"Post: {result['content']}")
db.close()
