# Master Ansatz Formalization

## Objetivo

Formalizar una familia efectiva compacta minima para el subconjunto de 7 eventos con `ringdown` congelado en `routeB_all18_20260422`, separando:

- un nucleo comun,
- una deformacion moderada,
- y un outlier robusto fuera de familia.

## Hechos Verificados

- Sobre los 7 eventos congelados:
  - Modelo A absorbe `4/7`
  - Modelo B absorbe `2/7`
  - `1/7` queda fuera de familia: `GW190503_185404`
- Las clases observadas en el subconjunto son:
  - `square_x3_plus_rational` = 3
  - `mixed_x0_x3_coupled` = 2
  - `linear_x3_rational` = 1
  - `x3_x1_bilinear` = 1

## Modelo A

Forma canonica propuesta:

```text
R ~ x2 * (C - x4/x1) + g(x3)
```

con:

```text
g(x3) = termino bajo en x3
```

admitiendo solo dos variantes compactas:

- correccion cuadratica: `a * (x3 - b)^2`
- correccion lineal: `a * x3 + b`

Lectura:

- `x2 * (C - x4/x1)` es el nucleo racional comun
- `g(x3)` captura la correccion baja minima necesaria
- no se introduce mezcla con `x0`

## Modelo B

Forma canonica propuesta:

```text
R ~ x2 * (C - x4/x1) + g(x3) + h(x0, x3)
```

con:

```text
h(x0, x3) = deformacion moderada de mezcla x0/x3
```

Lectura:

- Modelo B no reemplaza a A
- Modelo B solo existe para absorber la rama `mixed_x0_x3_coupled`
- no justifica abrir un segundo regimen completo

## Asignacion Final

Fuente tabular: `master_ansatz_assignment.csv`

| event | assignment | equation_class | lectura |
|---|---|---|---|
| GW150914 | A | square_x3_plus_rational | entra en el nucleo racional con correccion baja en x3 |
| GW170104 | B | mixed_x0_x3_coupled | requiere mezcla moderada x0/x3 ademas del nucleo |
| GW170814 | A | square_x3_plus_rational | entra en el nucleo racional con correccion baja en x3 |
| GW170823 | B | mixed_x0_x3_coupled | requiere mezcla moderada x0/x3 ademas del nucleo |
| GW190421_213856 | A | square_x3_plus_rational | entra en el nucleo racional con correccion baja en x3 |
| GW190503_185404 | outlier | x3_x1_bilinear | queda fuera de la familia minima |
| GW190828_063405 | A | linear_x3_rational | queda absorbido como correccion baja lineal en x3 |

## Evaluacion De Parsimonia

### Modelo A

Hecho verificado:

- absorbe los 3 dominantes
- absorbe ademas `GW190828_063405`

Formalizacion razonable:

- ya basta para sostener una familia efectiva compacta

### Modelo B

Hecho verificado:

- `GW170104` y `GW170823` no entran limpiamente en A
- ambos comparten mezcla moderada `x0/x3`

Formalizacion razonable:

- B si esta justificado
- pero como deformacion secundaria controlada, no como nuevo regimen

### Outlier

Hecho verificado:

- `GW190503_185404` exige un termino bilineal `x3*x1`
- no entra en A ni en B sin romper la simplicidad del ansatz

Interpretacion prudente:

- debe mantenerse fuera de familia minima por ahora

## Conclusion

La mejor lectura hoy es:

```text
familia efectiva compacta + deformacion moderada + outlier
```

En terminos operativos:

- **Modelo A** = familia base compacta suficiente para el nucleo
- **Modelo B** = extension minima y justificada para la rama `mixed_x0_x3_coupled`
- **GW190503_185404** = outlier robusto y separado

No se justifica todavia hablar de ley unica rigida.
Si se justifica usar esta formalizacion como hipotesis de trabajo compacta para el siguiente paso.
