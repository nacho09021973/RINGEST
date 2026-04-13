from google import genai

client = genai.Client(api_key="AIzaSyBYowChKeTP4YDM3ts3wprQYBpPGN9OX08")

print("Conectando con Gemini...")
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Escribe un enorme y sonoro "¡POR FIN!" seguido de una frase celebrando que se acabó esta tortura informática.'
)
print(response.text)
