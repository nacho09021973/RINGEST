import os
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1"
        self.headers = {'Content-Type': 'application/json'}
        self.model_url = None
        self.retryable_codes = {502, 503, 504}

    def autodiscover_model(self):
        """Consulta al servidor qué modelos están activos para esta Key."""
        print("🔍 [DISCOVERY] Consultando catálogo de modelos disponibles...")
        list_url = f"{self.base_url}/models?key={self.api_key}"
        try:
            r = requests.get(list_url, timeout=10)
            if r.status_code == 200:
                models = r.json().get('models', [])
                # Buscamos la versión más moderna disponible (2.5 > 2.0 > 1.5)
                for target in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
                    for m in models:
                        if target in m['name']:
                            self.model_url = f"{self.base_url}/{m['name']}:generateContent?key={self.api_key}"
                            print(f"🎯 [READY] Modelo detectado y vinculado: {m['name']}")
                            return True
            print(f"❌ [ERROR] No se encontró un modelo compatible. Status: {r.status_code}")
            return False
        except Exception as e:
            print(f"❌ [ERROR] Fallo en discovery: {e}")
            return False

    def send_with_backoff(self, payload, max_attempts=5):
        last_err = None
        for attempt in range(max_attempts):
            try:
                response = requests.post(self.model_url, headers=self.headers, json=payload, timeout=60)
                if response.status_code == 200:
                    return response.json()
                if response.status_code not in self.retryable_codes:
                    print(f"❌ [FATAL] {response.status_code}: {response.text}")
                    return None
                last_err = f"HTTP {response.status_code}"
            except Exception as e:
                last_err = str(e)

            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"⚠️ [RETRY {attempt+1}/{max_attempts}] {last_err}. Reintentando en {wait_time:.2f}s...")
            time.sleep(wait_time)
        return None

def main():
    client = GeminiClient()
    if not client.api_key:
        print("❌ [FAIL] GEMINI_API_KEY no configurada.")
        return

    # Paso maestro: Autodescubrimiento antes de empezar
    if not client.autodiscover_model():
        print("🚫 [ABORT] Imposible configurar el modelo automáticamente.")
        return

    print("\n🤖 Gemini CLI 'Discovery' v28 | RINGEST")
    historial = []

    while True:
        user_input = input("\nuser > ")
        if user_input.lower() in ['salir', 'exit', 'quit']: break

        if user_input.startswith("leer:"):
            archivo = user_input.split(":", 1)[1].strip()
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    prompt = f"Contenido de {archivo}:\n\n{f.read()}\n\nAnaliza este código."
                print(f"📖 {archivo} cargado.")
            except:
                print("❌ Archivo no encontrado."); continue
        else:
            prompt = user_input

        historial.append({"role": "user", "parts": [{"text": prompt}]})
        result = client.send_with_backoff({"contents": historial})
        
        if result:
            texto = result['candidates'][0]['content']['parts'][0]['text']
            print(f"\ngemini > {texto}")
            historial.append({"role": "model", "parts": [{"text": texto}]})

if __name__ == "__main__":
    main()