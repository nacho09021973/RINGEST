# Einstein-Radial Candidate

## Alcance

Este documento **no** afirma identificacion exacta de una EOM.
Formaliza una **proyeccion efectiva preferente** del nucleo empirico `A / B / outlier`
sobre una combinacion Einstein-radial del background EMD-like ya fijado en el run.

Se toma como contexto verificado:

- `master_ansatz_formalization.md`
- `master_ansatz_validation.md`
- `master_ansatz_assignment.csv`
- `master_ansatz_audit.csv`
- `master_ansatz_universality.csv`

No se reabre aqui la comparacion general con otros candidatos. La lectura operativa
es solo: **Einstein-radial primero; dilaton y gauge field quedan secundarios**.

## Background De Referencia

Ansatz de gauge ya usado en el repo:

```text
ds^2 = e^{2A(z)} [-f(z) dt^2 + dx^2] + dz^2 / f(z)
```

Reexpresion EMD-like ya verificada:

```text
x0 = A
x1 = f
x2 = A'
x3 = A''
x4 = f'
```

Base minima de bloques para comparar candidato y nucleo empirico:

- `A''`
- `A' * f'/f`
- `A'`
- `A'/z`
- `A'^2`
- `f''/f`
- y, solo para la deformacion `B`:
  `A + A''`
  `A * A''`

Observacion de repo ya fijada en el gauge geometrico:

```text
R = -2D A'' - D(D-1) A'^2 - (f'/f) A'
```

Eso hace natural que una lectura Einstein-radial efectiva viva sobre la subbase
`{A'', A' f'/f, A', A'/z, A'^2, f''/f}`.

## Candidata Einstein-Radial

La combinacion candidata se fija como:

```text
E_ER^eff
  = c1 A''
  + c2 A' (f'/f)
  + c3 A'
  + slow_bg[A'/z, A'^2, f''/f]
  + Delta_B
```

con:

```text
Delta_B = deformacion moderada controlada por (A + A'')
```

Lectura compacta:

- el **nucleo ganador** esta en `A' (C - f'/f)`;
- la parte en `A''` entra como **truncacion efectiva baja** del sector local;
- `A'/z`, `A'^2` y `f''/f` se reservan como **terminos lentos de background**
  que pueden renormalizar el offset o la pendiente sin ser exigidos por la
  familia minima observada;
- para `B` basta activar una deformacion moderada asociada a `A + A''`;
- **no hace falta** activar `A * A''` para la lectura minima preferente.

## Nucleo Empirico En La Misma Base

Del run actual:

```text
Modelo A:
R_emp ~ x2 * (C - x4/x1) + g(x3)

Modelo B:
R_emp ~ x2 * (C - x4/x1) + g(x3) + h(x0, x3)
```

Usando `x0 = A`, `x1 = f`, `x2 = A'`, `x3 = A''`, `x4 = f'`:

```text
Modelo A:
R_emp ~ A' (C - f'/f) + g(A'')

Modelo B:
R_emp ~ A' (C - f'/f) + g(A'') + deformacion(A + A'')
```

donde:

- `g(A'')` es baja: lineal o cuadratica en los eventos `A`;
- la rama `B` activa mezcla moderada `x0/x3`, o sea, una deformacion asociada
  a `A + A''`.

## Coincidencia De Bloques

| bloque | estado frente a la candidata Einstein-radial | lectura |
|---|---|---|
| `A' * f'/f` | coincidencia de bloques exacta | es el bloque racional comun del nucleo empirico |
| `A'` | coincidencia de bloques exacta | sale del termino `A' * C` del nucleo racional |
| `A''` | truncacion efectiva razonable | captura la parte baja `g(A'')`; exacta solo en la rama lineal, y localmente truncada en la rama cuadratica |
| `A'/z` | termino lento de background | no lo exige el ajuste empirico minimo; puede absorber deriva radial suave |
| `A'^2` | termino lento de background | natural en combinaciones Einstein, pero no necesario para sostener `A / B` |
| `f''/f` | termino lento de background | permitido como correccion lenta; no aparece como bloque exigido por el nucleo descubierto |
| `A + A''` | deformacion moderada para `B` | basta para leer la rama `mixed_x0_x3_coupled` sin abrir un segundo regimen |
| `A * A''` | no requerido en la lectura minima | se deja fuera por parsimonia |

## Que Reproduce Exactamente

La candidata Einstein-radial reproduce **exactamente** los dos bloques estructurales
que si son universales en los seis casos no outlier:

- `A' * f'/f`
- `A'`

Esos dos bloques son justamente la traduccion EMD-like de:

```text
x2 * (C - x4/x1)
```

que aparece en `master_ansatz_formalization.md`, `master_ansatz_validation.md`,
`master_ansatz_audit.csv` y `master_ansatz_universality.csv`.

## Que Parte Entra Como Truncacion O Termino Lento

### Truncacion efectiva

La parte `g(A'')` del Modelo A entra como truncacion efectiva baja:

- en `GW190828_063405` la lectura lineal en `x3` se proyecta directamente sobre `A''`;
- en `GW150914`, `GW170814` y `GW190421_213856` la correccion cuadratica en `x3`
  se interpreta como expansion local de bajo orden en torno a un background ya fijado.

No hace falta vender eso como igualdad exacta a una EOM radial cerrada.

### Termino lento de background

Los bloques:

- `A'/z`
- `A'^2`
- `f''/f`

se interpretan solo como sector lento de background disponible para absorber
renormalizaciones suaves de la proyeccion Einstein-radial. El nucleo empirico
actual no obliga a escribirlos explicitamente.

## Como Absorbe Modelo A

Modelo A queda absorbido como:

```text
A' (C - f'/f) + truncacion_baja(A'')
```

Hecho verificado en el run:

- cubre `GW150914`
- cubre `GW170814`
- cubre `GW190421_213856`
- cubre `GW190828_063405`

Interpretacion prudente:

- la parte universal es Einstein-radial;
- la parte en `A''` es la correccion local minima necesaria;
- no hace falta mezcla con `A`.

## Como Absorbe Modelo B

Modelo B se interpreta como una deformacion moderada de la misma candidata:

```text
E_ER^eff  ->  E_ER^eff + Delta_B
Delta_B ~ deformacion(A + A'')
```

Hecho verificado en el run:

- `GW170104` y `GW170823` conservan el mismo nucleo racional;
- ambos solo piden mezcla moderada `x0/x3`;
- no aparece el termino `x3*x1`.

Interpretacion prudente:

- `B` **no** define una familia nueva;
- `B` es una deformacion controlada del mismo nucleo Einstein-radial;
- la forma minima para esa deformacion es activar `A + A''`;
- no hace falta subir a `A * A''` en esta formalizacion.

## Por Que El Outlier Queda Fuera

`GW190503_185404` queda fuera porque exige:

```text
x3 * x1 = A'' * f
```

Ese bloque:

- no aparece en los otros seis casos,
- no pertenece a la base minima preferente de la candidata Einstein-radial,
- y no se absorbe en `A` ni en `B` sin romper parsimonia.

Por tanto:

- queda fuera de la familia compacta principal,
- no invalida la lectura Einstein-radial del nucleo,
- solo marca un canal bilineal adicional que hoy no conviene incorporar.

## Sintesis Operativa

La formalizacion preferente queda asi:

```text
nucleo empirico A/B
  -> proyeccion efectiva preferente sobre una combinacion Einstein-radial
  -> con coincidencia exacta en A' y A' f'/f
  -> con A'' tratado como truncacion baja
  -> con A'/z, A'^2 y f''/f relegados a background lento
  -> con B como deformacion moderada via (A + A'')
  -> con GW190503_185404 fuera por el bloque A'' * f
```

Eso deja fijada la lectura principal sin sobreactuar la evidencia:

- **si** hay una candidata Einstein-radial preferente para el nucleo empirico;
- **no** se esta afirmando identidad exacta con una EOM Einstein del bulk.
