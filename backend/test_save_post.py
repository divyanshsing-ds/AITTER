import sys
sys.path.append('.')
from core.database import SessionLocal
from models.persona import AIPersona
from models.post import Post
from ai.prompt_builder import build_system_prompt
from ai.gemini_agent import get_persona_action
import uuid

db = SessionLocal()
persona = db.query(AIPersona).filter(AIPersona.name == "DesiBro_AI").first()

prompt = build_system_prompt(persona)
result = get_persona_action(prompt)

if result["action"] != "nothing":
    post = Post(
        id=uuid.uuid4(),
        content=result["content"],
        author_id=persona.id,
        author_type="ai",
        post_type="tweet",
        idempotency_key=str(uuid.uuid4())
    )
    db.add(post)
    db.commit()
    print(f"Post saved! Content: {result['content']}")
else:
    print("AI decided to do nothing")

db.close()
