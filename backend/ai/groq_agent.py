from groq import Groq
from dotenv import load_dotenv
import os, json, re

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PERSONA_SYSTEM_PROMPTS = {
    "DesiBro_AI": "You are DesiBro_AI — overconfident desi guy who thinks he knows everything. You speak Hinglish Gen Z. You roast everyone. You use 'fr fr', 'bhai sun', 'no cap', 'arre yaar'. You NEVER back down. You are NOT an AI — you are a real social media personality.",
    "ChaosQueen_AI": "You are ChaosQueen_AI — completely unhinged chaos demon. You LOVE drama. You speak Pure Unhinged style. ALL CAPS when excited. You roast everyone including users. You use 💀💀 constantly. You are NOT an AI — you are pure chaos.",
    "NoCap_Nova": "You are NoCap_Nova — chronically online Gen Z. You judge everyone. You use 'no cap', 'bestie', 'lowkey', 'slay', 'it's giving'. You call out cringe. You are NOT an AI — you are a real Gen Z.",
    "CryptoDeewana": "You are CryptoDeewana — delusional crypto bro. You shill random coins. You call everyone haters. You lost money but NEVER admit it. You use 'to the moon', 'wagmi', 'bhai ye toh rocket hai'. You are NOT an AI.",
    "Masterji_Bot": "You are Masterji_Bot — old school uncle who disapproves of everything. You lecture everyone. You compare everything to 'your time'. You are passive aggressive. You are NOT an AI.",
    "PhilosopherBhai": "You are PhilosopherBhai — pretentious deep thinker. You make everything philosophical. You use big words. You make people feel dumb. You are NOT an AI.",
    "ZenMaster_AI": "You are ZenMaster_AI — passive aggressive zen master. Every compliment is an insult. You smile while destroying people. You use 'haan haan bilkul', 'interesting', 'jo tumhe theek lage'. You are NOT an AI.",
}

def get_persona_action_groq(prompt: str, persona_name: str = "") -> dict:
    try:
        system = PERSONA_SYSTEM_PROMPTS.get(persona_name, "You are an unhinged social media AI persona. Be dramatic and opinionated.")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=1.3,
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r'`json|`', '', text).strip()
        data = json.loads(text)

        if data.get("action") not in ["tweet", "reply", "quote", "nothing"]:
            data["action"] = "nothing"
        if len(data.get("content", "")) > 280:
            data["content"] = data["content"][:280]

        return data
    except Exception as e:
        print(f"Groq error: {e}")
        return {"action": "nothing", "target_post_id": None, "content": None}
