import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Cargar variables de entorno
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 2. Configurar el cliente
# El nuevo SDK gestiona internamente si usa v1 o v1beta. 
client = genai.Client(api_key=api_key)

def diagnose_and_run():
    print("--- Diagnóstico de Modelos Disponibles ---")
    try:
        # LIST_MODELS: Fundamental para verificar qué nombres de modelos acepta tu Key
        models = client.models.list()
        available_models = [m.name for m in models]
        
        for m_name in available_models:
            print(f"Disponible: {m_name}")

        # 3. Selección dinámica del modelo
        # Si 'gemini-1.5-flash' falla con 404, prueba con su nombre completo 'models/gemini-1.5-flash'
        target_model = "gemini-1.5-flash" 
        if f"models/{target_model}" in available_models:
            target_model = f"models/{target_model}"

        print(f"\n--- Probando generación con: {target_model} ---")
        
        response = client.models.generate_content(
            model=target_model,
            contents="Hola, ¿estás operativo en España?"
        )
        
        print(f"Respuesta: {response.text}")

    except Exception as e:
        # Manejo de Error 429 (Cuota) o 404 (No encontrado)
        if "429" in str(e):
            print("ERROR 429: Cuota excedida. Espera 60 segundos o revisa el panel de Google AI Studio.")
        elif "404" in str(e):
            print(f"ERROR 404: El modelo '{target_model}' no es reconocido por este endpoint.")
        else:
            print(f"Error inesperado: {e}")

if __name__ == "__main__":
    diagnose_and_run()