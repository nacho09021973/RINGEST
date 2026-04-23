# Einstein-Radial Best Combination

## Alcance

Este documento aprieta la lectura principal ya fijada:

```text
el nucleo empirico A/B se interpreta preferentemente como proyeccion efectiva
Einstein-radial del background
```

No se afirma identificacion exacta de una EOM.
No se reabre la comparacion con Schrodinger salvo como contexto ya resuelto:

- Einstein-radial = lectura principal
- Schrodinger = analogia formal seria, pero de segundo nivel

Aqui solo se pregunta:

```text
que combinacion Einstein-radial concreta es la mejor candidata
para generar el nucleo empirico A/B bajo truncacion efectiva razonable
```

## Background De Referencia

Ansatz de black-brane ya usado en el repo:

```text
ds^2 = e^{2A(z)} [-f(z) dt^2 + dx^2] + dz^2 / f(z)
```

Reexpresion EMD-like ya fijada:

```text
x0 = A
x1 = f
x2 = A'
x3 = A''
x4 = f'
```

Bloques de comparacion:

- `A''`
- `A' * f'/f`
- `A'`
- `A'/z`
- `(A')^2`
- `f''/f`
- y solo para `B`:
  `A + A''`
  `A * A''`

Hecho geometrico ya usado en el repo:

```text
R = -2D A'' - D(D-1) (A')^2 - (f'/f) A'
```

## Nucleo Empirico Reexpresado

Del run actual:

```text
Modelo A:
R_emp ~ A' (C - f'/f) + g(A'')

Modelo B:
R_emp ~ A' (C - f'/f) + g(A'') + deformacion(A + A'')
```

donde:

- `g(A'')` es baja: lineal o cuadratica;
- `B` activa solo mezcla moderada `A + A''`;
- el outlier introduce `A'' * f` y queda fuera.

## Combinaciones Einstein-Radiales Candidatas

### C1. Combinacion warp-blackening de primer orden

```text
E1^eff = A' (C - f'/f) + lambda A''
```

Lectura:

- `A' * f'/f` y `A'` quedan en primer plano;
- `A''` entra como correccion local baja;
- `A'/z`, `(A')^2` y `f''/f` quedan fuera del nucleo y pueden absorberse
  como fondo lento si hiciera falta.

Es la combinacion mas cercana a una restriccion radial efectiva del background
tras eliminar materia explicita y quedarse con el sector que si aparece en el run.

### C2. Combinacion radial tipo traza

```text
E2^eff = alpha A'' + beta A' (f'/f) + gamma (A')^2
```

Lectura:

- esta combinacion esta mas cerca de la estructura tipo traza/Ricci;
- captura bien `A''` y `A' * f'/f`;
- pero arrastra `(A')^2` como bloque estructural de primer nivel.

### C3. Combinacion radial mejorada por borde

```text
E3^eff = alpha A'' + beta A' (f'/f) + gamma A'/z
```

Lectura:

- puede ser razonable como combinacion radial con informacion de gauge radial
  o de comportamiento near-boundary;
- pero mete `A'/z` demasiado pronto;
- y no reproduce de forma tan limpia el bloque lineal `A'`.

## Proyeccion En La Base Comun

| bloque | C1 | C2 | C3 |
|---|---|---|---|
| `A' * f'/f` | coincidencia exacta | coincidencia exacta | coincidencia exacta |
| `A'` | coincidencia exacta | no aparece como bloque propio | no aparece como bloque propio |
| `A''` | truncacion efectiva razonable | coincidencia exacta | coincidencia exacta |
| `A'/z` | termino lento absorbido | ausente | coincidencia exacta pero sobrante |
| `(A')^2` | termino lento absorbido | coincidencia exacta pero sobrante | ausente |
| `f''/f` | termino lento absorbido | ausente | ausente |
| `A + A''` | deformacion moderada natural para `B` | no sale de forma minima | no sale de forma minima |
| `A * A''` | no requerido | no requerido | no requerido |

## Comparacion Contra El Nucleo A/B

### C1

Cobertura:

- reproduce **exactamente** el nucleo comun `A' (C - f'/f)`;
- admite `A''` como truncacion baja para `A`;
- deja sitio natural para `B` como deformacion moderada `A + A''`.

Parsimonia:

- maxima entre las candidatas;
- no obliga a promover `A'/z`, `(A')^2` ni `f''/f` al nucleo.

Compatibilidad:

- muy buena con `A`;
- muy buena con `B`;
- mantiene el outlier fuera sin tension.

### C2

Cobertura:

- reproduce bien `A''` y `A' * f'/f`;
- pero no reproduce de forma limpia el bloque lineal `A'`.

Parsimonia:

- peor que `C1`, porque convierte `(A')^2` en bloque estructural cuando el run
  no lo exige.

Compatibilidad:

- razonable para `A`;
- menos economica para `B`;
- no mejora el tratamiento del outlier.

### C3

Cobertura:

- reproduce `A''` y `A' * f'/f`;
- pero sustituye el bloque lineal `A'` por `A'/z`, que no es lo que sale
  dominante en el run.

Parsimonia:

- peor que `C1`, porque sube `A'/z` al nucleo sin necesidad empirica.

Compatibilidad:

- aceptable solo como variante secundaria;
- menos natural para `B`;
- tampoco absorbe el outlier.

## Ranking

```text
1. C1 = combinacion warp-blackening de primer orden
2. C2 = combinacion radial tipo traza
3. C3 = combinacion radial mejorada por borde
```

Razon del ranking:

- `C1` es la unica que reproduce a la vez los dos bloques dominantes exactos:
  `A' * f'/f` y `A'`;
- `C2` y `C3` son geometricamente razonables, pero promueven bloques que el run
  no necesita como nucleo;
- ninguna mejora la lectura del outlier.

## Mejor Combinacion Concreta

La mejor candidata concreta es:

```text
E1^eff = A' (C - f'/f) + lambda A''
```

Interpretacion prudente:

- no se propone como EOM exacta;
- se propone como la **mejor combinacion Einstein-radial efectiva** del background
  para generar el nucleo empirico A/B.

## Que Reproduce Exactamente

`E1^eff` reproduce **exactamente**:

- `A' * f'/f`
- `A'`

Esos son justamente los dos bloques universales del nucleo comun observado en
los seis casos no outlier.

## Que Parte Entra Solo Por Truncacion Efectiva

La parte:

```text
lambda A''
```

entra como truncacion efectiva razonable:

- exacta en la rama lineal de `A`;
- razonable como expansion local de bajo orden en la rama cuadratica.

No hace falta venderla como bloque universal exacto.

## Que Parte Queda Como Termino Lento De Background

Quedan como sector lento absorbido:

- `A'/z`
- `(A')^2`
- `f''/f`

Interpretacion:

- son bloques Einstein-radiales plausibles del background;
- pero el run actual no obliga a subirlos al nucleo dominante.

## Como Se Interpreta B

`B` se interpreta como deformacion moderada de `E1^eff`:

```text
E1^eff  ->  E1^eff + Delta_B
Delta_B ~ deformacion(A + A'')
```

Lectura:

- el nucleo no cambia;
- solo se activa mezcla moderada `A + A''`;
- no hace falta `A * A''`.

## Por Que El Outlier Sigue Fuera

`GW190503_185404` sigue fuera porque exige:

```text
A'' * f
```

Ese bloque:

- no pertenece al nucleo de `E1^eff`,
- no aparece en los otros seis casos,
- y no se absorbe con una deformacion moderada sin romper parsimonia.

## Veredicto

Veredicto prudente:

```text
la mejor combinacion Einstein-radial concreta es
E1^eff = A' (C - f'/f) + lambda A''
```

con la siguiente lectura operativa:

- coincidencia exacta en `A' * f'/f` y `A'`;
- `A''` como truncacion efectiva razonable;
- `A'/z`, `(A')^2` y `f''/f` como fondo lento absorbido;
- `B` como deformacion moderada via `A + A''`;
- outlier fuera por requerir `A'' * f`.

Eso deja la hipotesis principal en su forma mas concreta hasta ahora, sin
sobreactuar la evidencia.
