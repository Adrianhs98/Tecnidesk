import asyncio
import sys
from google import genai
from google.genai import types
from google.genai.errors import APIError

async def test_model(client: genai.Client, model_name: str):
    print(f"\n--- Probando modelo: {model_name} ---")
    try:
        response = await client.aio.models.generate_content(
            model=model_name,
            contents="Hola, responde solo con la palabra 'OK' si recibes este mensaje.",
            config=types.GenerateContentConfig(temperature=0.0)
        )
        print(f"✅ ÉXITO. Respuesta del modelo: {response.text}")
        return True
    except APIError as e:
        print(f"❌ ERROR DE API (APIError):")
        print(f"   Código: {e.code}")
        print(f"   Mensaje: {e.message}")
        print(f"   Estado: {e.status}")
        if e.code == 503:
            print("   -> DIAGNÓSTICO: Error 503 Service Unavailable. Esto significa que los servidores de Google para este modelo están saturados en este momento.")
        return False
    except Exception as e:
        print(f"❌ ERROR INESPERADO:")
        print(f"   Tipo: {type(e)}")
        print(f"   Detalle: {e}")
        return False

async def main():
    print("==================================================")
    print("   TEST DE DIAGNÓSTICO DE MODELOS GEMINI API")
    print("==================================================\n")
    
    api_key = input("Pega tu GEMINI_API_KEY aquí (y presiona Enter): ").strip()
    
    if not api_key:
        print("Error: No ingresaste ninguna API Key. Cancelando.")
        sys.exit(1)
        
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error al inicializar el cliente de Google GenAI: {e}")
        sys.exit(1)

    # Lista de modelos a probar (desde los más recientes a los más estables/antiguos)
    modelos_a_probar = [
        # Familia Gemini 3.x (Generación actual - Agosto 2026)
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.1-pro",
        "gemini-3.5-flash-lite",
        
        # Familia Gemini 2.5 (En proceso de retiro, pero estables hasta Octubre 2026)
        "gemini-2.5-flash",
        "gemini-2.5-pro"
    ]
    
    print("\nIniciando pruebas de conexión con los modelos...\n")
    
    for modelo in modelos_a_probar:
        await test_model(client, modelo)
        # Pequeña pausa para no saturar la API con rate limits
        await asyncio.sleep(1)
        
    print("\n==================================================")
    print("   PRUEBAS FINALIZADAS")
    print("==================================================")
    print("Revisa los resultados arriba para ver qué modelos respondieron con ✅ y cuáles devolvieron ❌.")

if __name__ == "__main__":
    asyncio.run(main())
