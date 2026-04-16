# Eventos canonicos

Datos pesados:

```text
data/gwosc_events/
```

`data/` esta ignorado por git. No commitear strain, HDF5, ringdown, geometria
inferida, checkpoints ni tablas enriquecidas.

## Layout

```text
data/gwosc_events/<EVENT>/
  raw/
  boundary/
  boundary/ringdown/
  boundary_dataset/
```

## Canario canonico

Usar estos 5 eventos para regresiones locales rapidas:

```text
GW150914
GW151012
GW170104
GW190521_030229
GW191109_010717
```

## Cohorte local completa

La cohorte completa local es todo directorio bajo `data/gwosc_events/` que tenga
subdirectorio `raw/`.

Listar:

```bash
find data/gwosc_events -mindepth 1 -maxdepth 1 -type d -exec test -d '{}/raw' \; -printf '%f\n' | sort
```

Contar:

```bash
find data/gwosc_events -mindepth 1 -maxdepth 1 -type d -exec test -d '{}/raw' \; -printf '%f\n' | wc -l
```

## Regla

Eventos reales: `data/gwosc_events/`.

Experimentos desechables: `runs/`.
