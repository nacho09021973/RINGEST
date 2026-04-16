import urllib.request
import json
import csv

# El enlace de Cardiff que has encontrado
URL = "https://data.cardiffgravity.org/gwcat-data/data/gwosc_gracedb.json"

print(f"Descargando catálogo desde Cardiff Gravity...")
response = urllib.request.urlopen(URL)
gwcat = json.loads(response.read().decode('utf-8'))

# En gwcat, los eventos suelen estar dentro de un diccionario principal llamado "data"
events = gwcat.get("data", gwcat)

csv_filename = "catalog_params.csv"
count = 0

with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["event", "M_final_Msun", "chi_final"])

    for ev_name, ev_data in events.items():
        m = float("nan")
        chi = float("nan")
        
        # En el JSON de Cardiff, la masa final suele llamarse 'Mfinal' y el espín 'af' o 'chif'
        # Y el valor central está en la clave 'best'
        m_data = ev_data.get("Mfinal")
        if isinstance(m_data, dict) and m_data.get("best") is not None:
            m = float(m_data["best"])
            
        chi_data = ev_data.get("af") or ev_data.get("chif")
        if isinstance(chi_data, dict) and chi_data.get("best") is not None:
            chi = float(chi_data["best"])
            
        # Lo guardamos en el CSV si encontramos al menos uno de los dos
        if not (m != m and chi != chi):  # Truco para comprobar si ambos son NaN
            writer.writerow([ev_name, m, chi])
            count += 1

print(f"¡Éxito! Se han extraído {count} eventos y guardado en '{csv_filename}'.")
print("Ya puedes ejecutar tu pipeline principal usando este CSV.")