from google import genai
try:
    client = genai.Client(api_key="")
except Exception as e:
    print("CRASHED:", repr(e))
