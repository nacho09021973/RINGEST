# Master Ansatz Validation

## Resumen

Sobre el subconjunto de 7 eventos con `ringdown` congelado, la hipotesis compacta

- **A** = nucleo racional + correccion baja en `x3`
- **B** = A + mezcla moderada `x0/x3`
- **outlier** = termino inequívoco `x3*x1`

queda validada internamente sin excepciones ad hoc.

## Reglas Minimas De Asignacion

### A

```text
R ~ x2 * (C - x4/x1) + g(x3)
```

con `g(x3)` baja, lineal o cuadratica.

Regla:

- hay nucleo racional `x2 * (C - x4/x1)`
- hay correccion baja en `x3`
- no hace falta mezcla `x0/x3`
- no aparece termino `x3*x1`

### B

```text
R ~ x2 * (C - x4/x1) + g(x3) + h(x0, x3)
```

Regla:

- se mantiene el nucleo racional
- hace falta mezcla moderada `x0/x3`
- no aparece termino `x3*x1`

### Outlier

Regla:

- aparece el termino bilineal `x3*x1`
- queda fuera de A y B sin forzar complejidad extra

## Asignacion Final De Los 7 Eventos

| event | assignment | equation_class |
|---|---|---|
| GW150914 | A | `square_x3_plus_rational` |
| GW170104 | B | `mixed_x0_x3_coupled` |
| GW170814 | A | `square_x3_plus_rational` |
| GW170823 | B | `mixed_x0_x3_coupled` |
| GW190421_213856 | A | `square_x3_plus_rational` |
| GW190503_185404 | outlier | `x3_x1_bilinear` |
| GW190828_063405 | A | `linear_x3_rational` |

## Por Que La Validacion Se Sostiene

### A Es Estable

Hecho verificado:

- los cuatro eventos asignados a A cumplen la misma regla estructural
- todos comparten nucleo racional
- todos se absorben con una correccion baja en `x3`
- ninguno necesita mezcla `x0/x3`
- ninguno contiene `x3*x1`

### B Esta Justificado

Hecho verificado:

- `GW170104` y `GW170823` no entran limpiamente en A
- ambos se absorben con una sola regla adicional comun: mezcla moderada `x0/x3`

Interpretacion prudente:

- B añade complejidad minima y justificada
- no abre un segundo regimen completo

### El Outlier Es Inequivoco

Hecho verificado:

- `GW190503_185404` es el unico caso con termino `x3*x1`
- esa marca no aparece en los otros seis eventos
- no entra en A ni en B sin romper la compacidad del ansatz

## Conclusion

La hipotesis compacta `A / B / outlier` es reproducible y no arbitraria.

Puede usarse ya como base de la siguiente fase de interpretacion fisica, manteniendo:

- **A** como familia efectiva compacta,
- **B** como deformacion moderada,
- **GW190503_185404** como outlier robusto separado.
