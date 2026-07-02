import os

import pytest
from dotenv import load_dotenv

pytestmark = [pytest.mark.unit]

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if api_key and api_key.startswith("sk-"):
    # Bewust GEEN key-karakters printen (ook geen prefix) — zie DEF-493.
    print("✅ OpenAI API key geladen (waarde niet getoond).")
else:
    print("❌ Geen geldige API key gevonden.")
