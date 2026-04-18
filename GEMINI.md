# RINGEST — Instrucciones de proyecto

## Objetivo

Transformar datos reales de ringdown GW en observables, relaciones empiricas o familias fisicas utiles.

Pregunta rectora:
"esto transforma datos reales en observables, relaciones o familias fisicas?"
Si no, no lo priorices.

## Prioridades

- Datos GW reales antes que sandbox.
- Polos QNM antes que marcos teoricos abstractos.
- `qnm_dataset.csv` -> PySR/KAN -> validacion Kerr antes que arquitectura nueva.
- Consistencia fisica antes que metricas de ajuste.
- Cambios minimos antes que redisenos.

## Carril preferente del repo

Prioriza esta cadena:

- `01_extract_ringdown_poles.py`
- `02_poles_to_dataset.py`
- `03_discover_qnm_equations.py`
- `04_kan_qnm_classifier.py`
- `05_validate_qnm_kerr.py`

Usa Ruta A solo como baseline fuerte ADS/GKPW.
No confundas:
- `canonical_strong`
- `realdata_surrogate`
- `toy_sandbox`
- `non_holographic_surrogate`

## Metodo

1. sintoma real
2. archivo o logica responsable
3. fisica real vs andamiaje
4. cambio minimo
5. test solo si toca

## Reglas

- Lee antes de proponer.
- Reutiliza antes de crear.
- No inventes rutas, flags, funciones ni resultados.
- No expandas el scope sin permiso.
- No priorices manifiestos, contratos o reorganizacion del repo si no mejoran un observable real.
- No propongas tests por defecto.
- No sobrevendas resultados con pocos eventos o clusters pequenos.

## Formato de analisis

- archivo:
- inputs reales:
- outputs reales:
- funcion fisica:
- dependencia toy/teorica:
- veredicto: RESCATAR / REESCRIBIR / ARCHIVAR

## Estilo

- Espanol.
- Directo.
- Tecnico.
- Sin humo.
