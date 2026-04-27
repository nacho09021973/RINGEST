import os
import unicodedata
import shutil
from pathlib import Path

def fix_rare_fonts(text: str) -> str:
    """Corrige mojibake y fuentes raras"""
    # Mojibake comun
    for enc_from, enc_to in [('cp1252', 'utf-8'), ('latin1', 'utf-8')]:
        try:
            fixed = text.encode(enc_from).decode(enc_to)
            if fixed != text:
                text = fixed
                break
        except:
            pass

    # Normalizar fuentes Unicode fancy
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.encode('ascii', errors='ignore').decode('ascii')
    
    return text


def fix_python_files(directory: str = ".", create_backup: bool = True):
    path = Path(directory).resolve()   # .resolve() ayuda mucho en WSL
    
    if not path.exists():
        print(f" La carpeta no existe: {path}")
        print(f"   Directorio actual: {Path.cwd()}")
        print(f"   Prueba con: .   o   /home/ignac/RINGEST")
        return

    print(f" Buscando .py en: {path}\n")

    fixed_count = 0
    total = 0

    for py_file in path.rglob("*.py"):
        if py_file.name.startswith(".") or "__pycache__" in str(py_file):
            continue

        total += 1
        try:
            with open(py_file, "r", encoding="utf-8", errors="replace") as f:
                original = f.read()

            fixed = fix_rare_fonts(original)

            if fixed == original:
                print(f" Sin cambios   {py_file.name}")
                continue

            if create_backup:
                backup = py_file.with_suffix(".py.bak")
                shutil.copy2(py_file, backup)
                print(f" Backup  {backup.name}")

            with open(py_file, "w", encoding="utf-8") as f:
                f.write(fixed)

            print(f" Corregido    {py_file.name}")
            fixed_count += 1

        except Exception as e:
            print(f" Error en {py_file.name}: {e}")

    print("\n" + "="*60)
    print(f" Proceso finalizado!")
    print(f"   Archivos encontrados : {total}")
    print(f"   Archivos corregidos  : {fixed_count}")
    print(f"   Backups creados      : {fixed_count if create_backup else 0}")
    print("="*60)


# ===================== EJECUCION =====================
if __name__ == "__main__":
    print("=== Arreglador Masivo de Fuentes Raras (WSL mejorado) ===\n")
    
    ruta = input("Ruta de la carpeta (Enter = carpeta actual): ").strip()
    
    if not ruta or ruta in (".", "./"):
        ruta = "."
    # Ayuda para WSL
    elif ruta.startswith("\\\\wsl"):
        ruta = "/home/ignac/RINGEST"   # puedes cambiar si tu usuario es diferente

    backup_resp = input("Crear backups (.bak)? (s/n - recomendado s): ").strip().lower()
    crear_backup = backup_resp != "n"

    fix_python_files(ruta, crear_backup)