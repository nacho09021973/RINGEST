# Checklist AGMOO — Familia `ads`

**Versión**: 1.0  
**Estado**: Contrato canónico activo  
**Fecha**: 2026-04-15  

---

## Propósito

Este documento formaliza el contrato mínimo que debe satisfacer cualquier
geometría o run de familia `ads` en el pipeline RINGEST para recibir una
interpretación holográfica válida.

El contrato distingue cuatro sub-clasificaciones y seis estados de veredicto.
Un run `ads` que no satisfaga los gates mínimos **no puede** recibir
interpretación holográfica fuerte.

---

## Sub-clasificaciones `ads`

| Clasificación      | Condición de asignación                                          |
|--------------------|------------------------------------------------------------------|
| `ads_pure`         | `z_h=None` o `z_h≤0`, `deformation≈0`, **y** Gate 6 completo   |
| `ads_thermal`      | `z_h > 0` (horizonte presente, temperatura finita)              |
| `ads_deformed`     | `deformation ≠ 0` (deformación suave explícita del warp factor) |
| `ads_toy_boundary` | `z_h=None` o `z_h≤0`, `deformation≈0`, Gate 6 **incompleto**   |

**Nota**: `ads_pure` solo se asigna si además se satisfacen los campos del
Gate 6 holográfico. En ausencia de esos campos, el caso T=0 sin deformación
cae en `ads_toy_boundary`.

---

## Tipos de correlador (`correlator_type`)

| Valor                          | Descripción                                               |
|-------------------------------|-----------------------------------------------------------|
| `HOLOGRAPHIC_WITTEN_DIAGRAM`  | Diagrama de Witten completo (AdS/CFT exacto)              |
| `GEODESIC_APPROXIMATION`      | Aproximación geodésica, AGMOO Sec. 3.5.1                  |
| `QNM_SURROGATE`               | Surrogate basado en modos quasinormales                   |
| `TOY_PHENOMENOLOGICAL`        | Modelo fenomenológico toy (power-law / thermal scaling)   |
| `UNKNOWN`                     | No se puede inferir del código disponible                 |

**Regla**: No inventar `HOLOGRAPHIC_WITTEN_DIAGRAM` si el código no lo implementa.
No dejar `UNKNOWN` salvo que genuinamente no pueda inferirse.

---

## Gates de validación

### Gate geométrico mínimo

Campos obligatorios en metadata:

- [ ] `family` = `"ads"`
- [ ] `d` (dimensión del boundary, entero ≥ 2)
- [ ] `z_h` (posición del horizonte; `None` o `0.0` indica T=0)

### Gate holográfico mínimo (Gate 6)

Campos del diccionario holográfico:

- [ ] `bulk_field_name` — nombre del campo escalar bulk
- [ ] `operator_name` — nombre del operador de frontera
- [ ] `m2L2` — masa al cuadrado en unidades de L²
- [ ] `Delta` — dimensión conforme del operador
- [ ] `bf_bound_pass` — cota de Breitenlöhner-Freedman satisfecha (`True/False`)
- [ ] `uv_source_declared` — fuente UV declarada (`True/False`)
- [ ] `ir_bc_declared` — condición de contorno IR declarada (`True/False`)

**Cota BF**: Para AdS_{d+1}, el requisito es `m²L² ≥ -(d/2)²`.  
Una violación implica inestabilidad taquiónica → `ADS_CONTRACT_FAIL`.

### Gate UV/IR

- [ ] `uv_source_declared = True`
- [ ] `ir_bc_declared = True`

Si ambos están declarados, el gate pasa. Si uno está ausente o es `False`,
el gate retorna `FRAGILE`.

---

## Estados de veredicto

| Estado                          | Condición                                                                      |
|---------------------------------|--------------------------------------------------------------------------------|
| `ADS_CONTRACT_FAIL`             | Cota BF violada, o campos geométricos críticos (`family`, `d`) ausentes        |
| `ADS_TEMPLATE_ONLY`             | `correlator_type=UNKNOWN` **o** Gate 6 ausente (sin excepción térmica)         |
| `ADS_THERMAL_TOY_ONLY`          | Gate 6 **presente** + térmico + correlador no-Witten                           |
| `ADS_UV_IR_FRAGILE`             | Gate 6 presente, Gate UV/IR retorna FRAGILE                                    |
| `ADS_HOLOGRAPHIC_PARTIAL_PASS`  | Gates geométrico y holográfico pasan; UV/IR no declarado                       |
| `ADS_HOLOGRAPHIC_STRONG_PASS`   | Todos los gates pasan completamente                                            |

> **Invariante clave**: `ADS_THERMAL_TOY_ONLY` requiere Gate 6 presente.
> La ausencia de Gate 6 bloquea siempre con `ADS_TEMPLATE_ONLY`, aunque el caso sea térmico.

### Lógica de prioridad (orden de evaluación)

```
1. BF bound violada o campos geométricos críticos ausentes → ADS_CONTRACT_FAIL
2. correlator_type = UNKNOWN → ADS_TEMPLATE_ONLY
   Gate 6 incompleto (cualquier clasificación) → ADS_TEMPLATE_ONLY
3. Gate 6 presente + ads_thermal + correlador ≠ HOLOGRAPHIC_WITTEN_DIAGRAM → ADS_THERMAL_TOY_ONLY
4. Gate UV/IR = FRAGILE → ADS_UV_IR_FRAGILE
5. Gate UV/IR = PASS → ADS_HOLOGRAPHIC_STRONG_PASS
6. Por defecto → ADS_HOLOGRAPHIC_PARTIAL_PASS
```

---

## Estado actual del repo (2026-04-15)

| Campo                   | Estado actual                                              |
|-------------------------|------------------------------------------------------------|
| `ads_classification`    | `ads_thermal` (todos los prototipos tienen `z_h=1.0`)      |
| `correlator_type`       | `GEODESIC_APPROXIMATION` (`correlator_2pt_geodesic`)       |
| Gate 6 completo         | **NO** — `uv_source_declared`, `ir_bc_declared`, `bulk_field_name`, `operator_name`, `bf_bound_pass` ausentes |
| Veredicto esperado      | **`ADS_TEMPLATE_ONLY`**                                    |

**Justificación**:
- Todos los prototipos `ads` actuales (`ads_d3_Tfinite`, etc.) tienen horizonte → `ads_thermal`.
- El correlador usa `correlator_2pt_geodesic` → `GEODESIC_APPROXIMATION`.
- No existen campos del Gate 6 holográfico en los HDF5 generados actualmente.
- Gate 6 ausente bloquea con `ADS_TEMPLATE_ONLY` **antes** de evaluar si el caso es térmico.
  (`ADS_THERMAL_TOY_ONLY` solo es alcanzable cuando Gate 6 está **presente**.)

**Deuda contractual registrada**:
- `correlator_2pt_geodesic` tiene un fallback silencioso a `correlator_2pt_thermal` cuando
  el cálculo geodésico falla. El campo `correlator_type = GEODESIC_APPROXIMATION` refleja
  el camino principal, no el fallback interno. Pendiente: declarar el fallback explícitamente
  en metadata cuando ocurra.

---

## Campos de metadata canónica para `ads`

Campos que deben escribirse en HDF5 attrs y manifest para familia `ads`:

```
ads_classification     str   Una de {ads_pure, ads_thermal, ads_deformed, ads_toy_boundary}
correlator_type        str   Una de los CORRELATOR_TYPES canónicos
```

Campos opcionales del Gate 6 (cuando estén disponibles):

```
bulk_field_name        str   Nombre del campo escalar bulk
operator_name          str   Nombre del operador CFT
m2L2                   float Masa cuadrada en unidades L²
Delta                  float Dimensión conforme
bf_bound_pass          bool  Cota BF satisfecha
uv_source_declared     bool  Fuente UV declarada
ir_bc_declared         bool  CC IR declarada
```

---

## Archivos relevantes

| Archivo                            | Rol                                              |
|------------------------------------|--------------------------------------------------|
| `family_registry.py`               | Constantes canónicas: clasificaciones, tipos     |
| `tools/validate_agmoo_ads.py`      | Validador programático: gates + veredicto        |
| `01_generate_sandbox_geometries.py`| Escribe `ads_classification`, `correlator_type`  |
| `tests/test_agmoo_ads_contract.py` | Tests de contrato                                |

---

## Invariantes de diseño

1. **Conservador por defecto**: en ausencia de información, el veredicto cae al estado más restrictivo válido.
2. **Sin física inventada**: no se declara `ads_pure` ni `ADS_HOLOGRAPHIC_STRONG_PASS` sin evidencia.
3. **Derivado del código**: la clasificación se infiere del código real, no de supuestos externos.
4. **No romper familias no-ads**: el validador retorna `NOT_ADS` limpiamente para otras familias.
5. **Artefactos explícitos**: los campos se escriben en HDF5 attrs y manifest, no solo en logs.
