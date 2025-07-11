import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if api_key and api_key.startswith("sk-"):
    print(f"✅ OpenAI API key geladen: {api_key[:8]}...********")
else:
    print("❌ Geen geldige API key gevonden.")