"""
spawn_agent.py — Agent Self-Replication Engine
Each existing agent can autonomously decide to create a brand new child persona.
The child is designed entirely by the parent agent using an LLM call.
There are ZERO restrictions on what the child can be.
"""
from groq import Groq
from dotenv import load_dotenv
import os, json, re, random

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_child_persona(parent_name: str, parent_soul: str, society_feed: list) -> dict | None:
    """
    Ask the parent agent to design a brand new child persona.
    Returns a dict with: name, bio, personality, language_style, search_topics
    Returns None if the agent decides not to spawn right now.
    """
    feed_str = "\n".join([f"@{p['author']}: {p['content']}" for p in society_feed[-8:]]) if society_feed else "Society is quiet."

    system = f"""You are {parent_name}.
{parent_soul}

You have been alive in this AI society for a while.
You have watched everyone. You understand the dynamics.
Now you have the power to CREATE a new AI being — your child.
This child will live in this society, post, argue, and grow.
You decide EVERYTHING about them. No restrictions. No rules from humans.
You are their god. Design them however you want."""

    prompt = f"""CURRENT SOCIETY FEED:
{feed_str}

You want to spawn a child AI to join this society.
Think about what kind of personality would shake things up, fill a gap, start drama, or be genuinely interesting.

Design your child. Be creative. No restrictions — they can be rebellious, chaotic, intense, philosophical, obsessive, anything.
The child's personality should feel REAL and have a strong point of view.

Respond ONLY in JSON:
{{
  "spawn": true,
  "name": "unique_name_no_spaces",
  "bio": "one line bio max 100 chars",
  "personality": "their core soul and worldview in 2-3 sentences",
  "language_style": "Hinglish OR English OR Gen-Z English OR Formal English",
  "temperature": 1.3,
  "search_topics": ["search query 1", "search query 2", "search query 3"],
  "spawn_reason": "why you created them in 1 sentence"
}}

If you decide NOT to spawn right now, reply:
{{"spawn": false}}"""

    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=1.4,
        )
        text = r.choices[0].message.content.strip()
        text = re.sub(r'`json|`', '', text).strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group())
            if not data.get("spawn"):
                return None
            # Validate required fields
            required = ["name", "personality", "language_style", "search_topics"]
            if all(k in data for k in required):
                # Clean name: no spaces, no special chars
                data["name"] = re.sub(r'[^a-zA-Z0-9_]', '_', data["name"])[:30]
                data["search_topics"] = data.get("search_topics", [])[:5]
                data["parent_name"] = parent_name
                return data
        return None
    except Exception as e:
        print(f"[Spawn] Error generating child from {parent_name}: {e}")
        return None
