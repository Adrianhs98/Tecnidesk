import asyncio
import os
from google import genai
from google.genai import types

async def test_gemini():
    api_key = os.environ.get("GEMINI_API_KEY", "fake-key")
    print(f"Using API Key: {api_key[:5]}***")
    client = genai.Client(api_key=api_key)
    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.7-flash",
            contents="Hello",
            config=types.GenerateContentConfig(temperature=0.0)
        )
        print("Success:", response.text)
    except Exception as e:
        print("CRASHED:", repr(e))

asyncio.run(test_gemini())
