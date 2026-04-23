# Einstein-Radial Vs Schrodinger

## Alcance

Comparacion cerrada entre dos lecturas para el nucleo empirico `A/B` ya validado:

1. proyeccion efectiva **Einstein-radial** del background
2. lectura tipo **potencial efectivo de Schrodinger** para fluctuaciones

No se afirma prueba definitiva.
Se distingue entre:

- coincidencia exacta de bloques,
- coincidencia solo por truncacion,
- analogia formal de segundo nivel.

Base factual usada:

- `master_ansatz_formalization.md`
- `master_ansatz_validation.md`
- `master_ansatz_assignment.csv`
- `master_ansatz_audit.csv`
- `master_ansatz_universality.csv`
- `einstein_radial_candidate.md`

## Base Comun

Gauge de referencia del background:

```text
ds^2 = e^{2A(z)} [-f(z) dt^2 + dx^2] + dz^2 / f(z)
```

Identificacion EMD-like ya fijada:

```text
x0 = A
x1 = f
x2 = A'
x3 = A''
x4 = f'
```

Base minima de comparacion:

- `A''`
- `A' * f'/f`
- `A'`
- `A'/z`
- `(A')^2`
- `f''/f`
- y solo para `B`:
  `A + A''`
  `A * A''`

Nucleo empirico observado:

```text
Modelo A:
R_emp ~ A' (C - f'/f) + g(A'')

Modelo B:
R_emp ~ A' (C - f'/f) + g(A'') + deformacion(A + A'')
```

## Candidata Einstein-Radial

Forma ya formalizada:

```text
E_ER^eff
  = c1 A''
  + c2 A' (f'/f)
  + c3 A'
  + slow_bg[A'/z, (A')^2, f''/f]
  + Delta_B
```

con:

```text
Delta_B ~ deformacion(A + A'')
```

Punto fuerte ya verificado:

- reproduce **exactamente** `A' * f'/f`
- reproduce **exactamente** `A'`
- trata `A''` como truncacion baja razonable

## Candidata Schrodinger

Forma de referencia, lo mas justa y compacta posible para una fluctuacion lineal
sobre el mismo background, tras reduccion a variable maestra:

```text
-Psi'' + V_Sch(z) Psi = omega^2 Psi
```

con potencial efectivo generico:

```text
V_Sch^eff
  = f(z)^2 [u1 A'' + u2 (A')^2 + u3 A'/z + u4 / z^2]
  + f(z) f'(z) [v1 A' + v2 / z]
  + w1 f(z) f''(z)
```

Para compararla limpiamente con el nucleo descubierto, la proyeccion natural es
quitar el factor global de blackening y mirar:

```text
V_Sch^eff / f
  ~ f [u1 A'' + u2 (A')^2 + u3 A'/z + u4 / z^2]
  + f' [v1 A' + v2 / z]
  + w1 f''
```

o, en la base comun:

- `A' * f'/f` aparece de forma **exacta** solo tras esta normalizacion;
- `A''` aparece multiplicado por `f`, luego su coincidencia con el nucleo es
  **solo por reescalado/truncacion**;
- `(A')^2`, `A'/z` y `f''/f` aparecen de forma **natural y dominante**;
- el bloque `A'` solo entra si se añade una escala radial externa o una
  reparametrizacion adicional;
- la deformacion `A + A''` de la rama `B` no sale como estructura minima natural
  del potencial de fluctuaciones.

Esta es una candidata seria, no una caricatura: precisamente porque un potencial
de Schrodinger de fluctuaciones suele mezclar `A''`, `(A')^2`, `A'/z`,
`f' A'` y `f''`.

## Comparacion En La Misma Base

| bloque | Einstein-radial | Schrodinger |
|---|---|---|
| `A' * f'/f` | coincidencia exacta de bloques | coincidencia exacta solo tras normalizar por un factor global de `f` |
| `A'` | coincidencia exacta de bloques | no es bloque minimo natural; requiere reparametrizacion o escala extra |
| `A''` | truncacion efectiva razonable | aparece de forma natural, pero tipicamente vestido por `f`; coincidencia no tan limpia |
| `A'/z` | termino lento opcional | bloque natural del potencial, por tanto mas dificil de apagar |
| `(A')^2` | termino lento opcional | bloque natural del potencial, por tanto mas dificil de apagar |
| `f''/f` | termino lento opcional | bloque natural del potencial, por tanto mas dificil de apagar |
| `A + A''` | deformacion moderada natural para `B` | no emerge como bloque minimo de primer nivel |
| `A * A''` | no requerido | tampoco requerido, pero tampoco mejora la cobertura de `B` |

## Cobertura De Bloques

### Einstein-radial

Hecho verificado:

- captura directamente el nucleo comun `A' (C - f'/f)`;
- deja `A''` como correccion baja;
- absorbe `B` con una sola deformacion moderada `A + A''`.

Resultado:

- cobertura mas limpia del nucleo `A/B`.

### Schrodinger

Lectura prudente:

- si puede imitar parte del nucleo, sobre todo el sector `A' f'/f` y la presencia
  de `A''`;
- pero lo hace al precio de arrastrar de forma natural bloques adicionales
  `A'/z`, `(A')^2` y `f''/f`;
- ademas no genera de forma limpia el bloque lineal `A'` que si es dominante
  en el ansatz empirico;
- y la rama `B` no cae de manera tan economica en la estructura minima del potencial.

Resultado:

- cobertura parcial real,
- pero peor alineada con los bloques dominantes del descubrimiento.

## Parsimonia

Einstein-radial gana en parsimonia porque:

- coincide exactamente con dos bloques dominantes del nucleo;
- solo necesita tratar `A''` como truncacion baja;
- relega `A'/z`, `(A')^2` y `f''/f` a fondo lento no obligatorio;
- absorbe `B` con una sola deformacion moderada.

Schrodinger pierde parsimonia porque:

- para ser justo, su forma minima ya trae varios bloques adicionales naturales;
- el bloque `A'` no aparece de manera tan inmediata;
- y la lectura de `B` queda menos directa.

## Nivel Del Objeto

Este punto pesa.

El pipeline produjo un objeto que ya fue reexpresado como informacion del
**background**:

- `x0 = A`
- `x1 = f`
- `x2 = A'`
- `x3 = A''`
- `x4 = f'`

La lectura Einstein-radial vive en ese mismo nivel.

La lectura Schrodinger vive un nivel mas abajo:

- no es ecuacion del background,
- es ecuacion de una fluctuacion o variable maestra construida sobre el background,
- y por tanto su coincidencia con el nucleo descubierto es una analogia formal de
  segundo nivel, no una lectura del mismo objeto geometrico que produjo el pipeline.

Eso no la invalida, pero si la hace menos natural aqui.

## Respuestas Explicitas

### La candidata Schrodinger reproduce mejor, igual o peor los bloques dominantes

Peor.

Motivo:

- reproduce de forma plausible `A''` y `A' * f'/f`,
- pero `A' * f'/f` queda mas limpio en Einstein-radial,
- y el bloque `A'` no sale de forma tan directa ni tan economica.

### Requiere mas terminos sobrantes

Si.

Los bloques `A'/z`, `(A')^2` y `f''/f` son naturales en Schrodinger y por tanto
cuesta mas justificar su ausencia efectiva en el nucleo observado.

### Esta a un nivel menos natural que Einstein-radial para el objeto producido

Si.

Einstein-radial opera en el nivel del background.
Schrodinger opera en el nivel de fluctuacion sobre el background.

### Einstein-radial sigue ganando de forma prudente

Si.

Gana por:

- mejor coincidencia exacta con los bloques dominantes,
- menor sobrecarga estructural,
- y mejor nivel ontologico respecto al objeto que realmente produjo el pipeline.

## Veredicto

Veredicto prudente final:

```text
Einstein-radial sigue siendo la mejor lectura
```

Matiz falsable:

- la candidata Schrodinger **compite de verdad** como analogia formal de segundo nivel;
- pero en este run no supera ni iguala a Einstein-radial en cobertura limpia,
  parsimonia y nivel correcto del objeto.

Por tanto la hipotesis principal sale reforzada, no cerrada de forma definitiva.
