# Brand Guide

Paquete minimo de identidad visual provisional para Claude Design.

## Tono visual

Limpio, corporativo, sobrio y no decorativo. Priorizar legibilidad, contraste suave y ritmo vertical estable.

## Tipografia fallback recomendada

- Sans principal: `"Brand Sans", "Source Sans 3", Inter, "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
- Sans alternativa corta: `"Brand Sans", "Source Sans 3", "IBM Plex Sans", system-ui, sans-serif`
- Monospace de apoyo: `"IBM Plex Mono", "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace`

## Fuentes locales incluidas

- `design/fonts/SourceSans3-wght.ttf`
- `design/fonts/SourceSans3-Italic-wght.ttf`
- Uso recomendado: exponerlas como `Brand Sans` via `@font-face` y dejar fallbacks seguros detras

## Jerarquia tipografica

### H1

- Uso: titulares de pagina y hero corto
- Tamano: `48px`
- Line height: `1.1`
- Peso: `700`
- Tracking: `-0.02em`

### H2

- Uso: secciones principales
- Tamano: `32px`
- Line height: `1.2`
- Peso: `600`
- Tracking: `-0.01em`

### Body

- Uso: texto principal, UI copy, formularios
- Tamano: `16px`
- Line height: `1.6`
- Peso: `400`
- Tracking: `0`

### Caption

- Uso: etiquetas auxiliares, notas, metadata
- Tamano: `13px`
- Line height: `1.45`
- Peso: `500`
- Tracking: `0.01em`

## Pesos y tamanos recomendados

- `400`: cuerpo y texto largo
- `500`: labels, caption, botones
- `600`: subtitulos y enfasis estructural
- `700`: titulares

- `13px`: caption
- `14px`: body-small
- `16px`: body
- `20px`: lead corto
- `32px`: h2
- `48px`: h1

## Espaciado y grid

- Unidad base: `4px`
- Escala recomendada: `4, 8, 12, 16, 24, 32, 48, 64`
- Max width de contenido: `720px` para lectura, `1200px` para layout
- Grid recomendado:
  - mobile: `4` columnas, gutter `16px`, margen `16px`
  - tablet: `8` columnas, gutter `24px`, margen `24px`
  - desktop: `12` columnas, gutter `24px`, margen `32px`
- Ritmo vertical: usar multiplos de `8px` entre bloques

## Paleta minima neutra

- `canvas`: `#F7F7F5`
- `surface`: `#FFFFFF`
- `surface-muted`: `#F1F2EF`
- `text`: `#14171A`
- `text-muted`: `#586069`
- `border`: `#D7DBD4`
- `accent`: `#2F4758`
- `accent-strong`: `#1F3341`

## Radios sugeridos

- `4px`: inputs densos
- `8px`: cards, botones, contenedores base
- `12px`: paneles destacados

## Uso recomendado en Claude Design

- Mantener fondos claros y densidad baja.
- Evitar gradientes llamativos, sombras pesadas y formas ornamentales.
- Reservar el color acento para enlaces, botones primarios y estados de foco.
