import asyncio
import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

load_dotenv('backend/.env')

async def eval_model(client, model_name):
    print(f"==================================================")
    print(f"Probando: {model_name}")
    prompt = "Eres un técnico de reparación de celulares. Un cliente dice que su teléfono no da imagen pero cuando lo conecta a la PC, hace el sonido de conexión USB. Dame un diagnóstico rápido y directo en exactamente 2 oraciones cortas."
    
    start_time = time.time()
    try:
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2)
        )
        elapsed = time.time() - start_time
        print(f"Estado: ✅ ÉXITO")
        print(f"Tiempo de respuesta: {elapsed:.2f} segundos")
        print(f"Respuesta:\n{response.text}\n")
    except APIError as e:
        elapsed = time.time() - start_time
        print(f"Estado: ❌ FALLO (HTTP {e.code})")
        print(f"Tiempo hasta fallo: {elapsed:.2f} segundos")
        print(f"Mensaje de error: {e.message}\n")
    except Exception as e:
        print(f"Estado: ❌ FALLO (Inesperado)")
        print(f"Error: {e}\n")

async def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("API Key no encontrada en backend/.env")
        return
        
    client = genai.Client(
        api_key=api_key,
        http_options={"timeout": 5000} # Small timeout?
    )
    # The retry options might be under http_options in this new client
    
    modelos = [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.1-pro",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash"
    ]
    
    for mod in modelos:
        await eval_model(client, mod)
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
