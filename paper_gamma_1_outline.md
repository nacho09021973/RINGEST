# Paper Gamma 1 — Outline mínimo

## Título provisional
A pre-registered null audit of RINGEST on public GWTC-4.0/O4a ringdown data

## Tesis del paper
Presentamos un pipeline reproducible de auditoría sobre observables QNM publicados.
El resultado principal acepta explícitamente el NULL bajo el protocolo predefinido.

## Lo que este paper afirma
- El pipeline corre sobre datos públicos.
- El criterio NULL fue definido antes de la interpretación.
- La auditoría de fuente impide reinterpretar tensiones aparentes sin trazabilidad.
- La descomposición Shapley identifica qué variables sostienen la clasificación/score.
- En los 6 eventos solapados se separan observables robustos de dependencias de fuente.

## Lo que este paper no afirma
- No afirma nueva física.
- No afirma violación de Kerr.
- No afirma evidencia holográfica fuerte.
- No generaliza más allá de la cohorte auditada.

## Secciones

1. Introduction
2. Data and public provenance
3. Pre-registered NULL protocol
4. Pipeline and observables
5. Source audit
6. Shapley decomposition
7. Six-event overlap table
8. Results: NULL accepted
9. Discussion
10. Limitations
11. Outlook: standardized QNM uncertainty audit

## Figura mínima
- Flowchart del protocolo: public data → canonical table → NULL test → source audit → result.

## Tabla mínima
- 6 eventos solapados:
  - event_id
  - source
  - f_220
  - sigma_f
  - tau/gamma
  - sigma_tau/gamma
  - Kerr residual if available
  - source-consistency flag
  - paper verdict

## Nota sobre Ruta C (distinción crítica)
La Ruta C eliminada (2026-04-20) usaba extracción ESPRIT propia sobre strain crudo: no identificaba limpiamente el modo (2,2,0) y fue descartada.
El contraste Kerr en este paper usa QNM de literatura publicada (`data/qnm_events_literature.yml`, tabla Berti 2009, interpolación Kerr para chi_final) como input canónico. No son la misma cosa.

## Frase de cierre segura
The main result is not a claimed deviation from Kerr, but a reproducible negative result under an explicitly declared protocol.
