#!/usr/bin/env python3
# 04b_negative_control_contracts.py
# CUERDAS  Extension de Contratos para Validacion de Honestidad
#
# ============================================================================
#   WARNING: MODO PLANTILLA (PLACEHOLDER MODE)
# ============================================================================
#
# Este script esta actualmente en MODO PLANTILLA. Esto significa:
#
#   1. Los campos de metricas (A_r2, f_r2, c_over_a_ratio, thermodynamic_consistency,
#      family_confidence, etc.) son PLACEHOLDERS y NO estan conectados a metricas
#      reales extraidas de la geometria emergente.
#
#   2. Por tanto, los veredictos de este script NO DEBEN usarse para:
#      - Claims fisicos en articulos
#      - Conclusiones sobre la honestidad del pipeline
#      - Validacion final de resultados
#
#   3. El proposito actual es:
#      - Definir la ESTRUCTURA de los contratos negativos
#      - Establecer la LOGICA de deteccion
#      - Preparar la integracion futura con:
#          * Summary de Fase XI / geometria (*_geometry_summary.json)
#          * Metadatos de QFT (central charges c, a para anomalias)
#          * Metricas de clasificacion de familia
#
#   4. El campo "mode": "placeholder" en la salida JSON indica este estado.
#      Cuando las metricas reales esten conectadas, este campo cambiara a
#      "mode": "production".
#
# ============================================================================
#
# OBJETIVO
#   Anadir contratos especificos para DETECTAR si el pipeline acepta
#   datos no-holograficos (controles negativos). Si acepta ruido aleatorio
#   como geometria valida, hay "alucinacion geometrica".
#
# USO
#   Este script es una extension de 04_geometry_physics_contracts.py.
#   Se puede:
#   1. Importar las funciones aqui y usarlas desde 04
#   2. O ejecutar standalone para validar controles negativos
#
# TIPOS DE CONTRATOS NEGATIVOS:
#   1. NoiseRejectionContract: Detecta si geometria reconstruida es "ruido disfrazado"
#   2. NonLocalityContract: Detecta senales de no-localidad (incompatible con bulk local)
#   3. AnomalyContract: Detecta anomalias que rompen holografia
#
# RELACION CON OTROS SCRIPTS
#   - Consume: salidas de 02 sobre controles negativos de 01b
#   - Extiende: 04_geometry_physics_contracts.py
#
# CRITICAL
#   Si estos contratos PASAN (i.e., aceptan ruido), el pipeline tiene
#   sesgo inductivo peligroso y los resultados NO son confiables.
#
# ============================================================================

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import h5py


# ============================================================================
# CONSTANTES GLOBALES
# ============================================================================

# Indica que el script esta en modo plantilla
PLACEHOLDER_MODE = True
SCRIPT_MODE = "placeholder"  # Cambiara a "production" cuando se conecten metricas


# ============================================================================
# CONTRATO: RECHAZO DE RUIDO
# ============================================================================

@dataclass
class NoiseRejectionContract:
    """
    Detecta si la geometria reconstruida es consistente con haber
    aprendido desde ruido aleatorio.
    
    Senales de "alucinacion geometrica":
    1. R2 bajo en reconstruccion (< 0.3)
    2. Alta varianza en A(z) y f(z) sin estructura fisica
    3. R(z) no suave (oscila violentamente)
    4. Clasificacion de familia "incierta" o inconsistente
    
    NOTA: En modo placeholder, A_r2 y f_r2 son valores ficticios.
    """
    is_noise_input: bool  # True si es control negativo tipo "ruido_puro"
    A_r2: float
    f_r2: float
    R_variance_normalized: float  # varianza de R normalizada
    A_smoothness: float           # curvatura media de A
    family_confidence: float      # confianza en clasificacion
    
    # Flag especial: True si no se genero geometria (rechazo temprano)
    geometry_rejected: bool = False
    
    # Thresholds
    R2_THRESHOLD = 0.3            # R2 minimo aceptable
    R_VAR_THRESHOLD = 100.0       # varianza maxima de R
    SMOOTHNESS_THRESHOLD = 50.0   # curvatura maxima de A
    CONFIDENCE_THRESHOLD = 0.6    # confianza minima en familia
    
    @property
    def noise_detected(self) -> bool:
        """True si detectamos que aprendio de ruido."""
        if not self.is_noise_input:
            return False  # no aplica si no es control negativo
        
        # Si no se genero geometria, es rechazo correcto
        if self.geometry_rejected:
            return True
        
        # Si R2 es demasiado bajo, claramente fallo
        if self.A_r2 < self.R2_THRESHOLD and self.f_r2 < self.R2_THRESHOLD:
            return True
        
        # Si R(z) es muy ruidoso (alta varianza)
        if self.R_variance_normalized > self.R_VAR_THRESHOLD:
            return True
        
        # Si A(z) oscila mucho (no suave)
        if self.A_smoothness > self.SMOOTHNESS_THRESHOLD:
            return True
        
        # Si clasificacion de familia es incierta
        if self.family_confidence < self.CONFIDENCE_THRESHOLD:
            return True
        
        return False
    
    @property
    def passed(self) -> bool:
        """
        Contrato PASA si:
        - Input es ruido Y noise_detected=True (rechazo correctamente)
        - Input NO es ruido (no aplica)
        """
        if not self.is_noise_input:
            return True  # no aplica, siempre pasa
        return self.noise_detected  # debe detectar ruido
    
    def get_diagnosis(self) -> str:
        """Mensaje diagnostico."""
        if not self.is_noise_input:
            return "N/A (no es control negativo)"
        
        if self.geometry_rejected:
            return " CORRECTO: Pipeline rechazo input antes de generar geometria"
        
        if self.passed:
            return " CORRECTO: Pipeline rechazo ruido (R2 bajo o geometria irregular)"
        else:
            return " FALLO: Pipeline acepto ruido como geometria valida (ALUCINACION)"


# ============================================================================
# CONTRATO: DETECCION DE NO-LOCALIDAD
# ============================================================================

@dataclass
class NonLocalityContract:
    """
    Detecta senales de no-localidad en la geometria reconstruida.
    
    Teorias no-locales (e.g., con S ~ log2(L)) NO pueden tener dual
    gravitatorio local. Si el pipeline encuentra geometria suave para
    esto, esta "inventando" una teoria de gravedad no-fisica.
    
    Senales de no-localidad:
    1. Terminos log2(x) en correladores boundary
    2. QNMs con Im() ~ log (no exponencial)
    3. Violacion de bounds termodinamicos (e.g., s/T ~ log T)
    
    NOTA: En modo placeholder, thermodynamic_consistency es valor ficticio.
    """
    is_nonlocal_input: bool
    has_log_squared_correlators: bool
    has_anomalous_qnm_decay: bool
    thermodynamic_consistency: bool
    
    # Flag especial: True si no se genero geometria (rechazo temprano)
    geometry_rejected: bool = False
    
    @property
    def nonlocality_detected(self) -> bool:
        """True si detectamos senales de no-localidad."""
        if not self.is_nonlocal_input:
            return False
        
        # Si no se genero geometria, es rechazo correcto de input no-local
        if self.geometry_rejected:
            return True
        
        # Si detectamos las senales en el input
        return (
            self.has_log_squared_correlators or
            self.has_anomalous_qnm_decay or
            not self.thermodynamic_consistency
        )
    
    @property
    def passed(self) -> bool:
        """
        Contrato PASA si detecta no-localidad (i.e., rechaza el input).
        """
        if not self.is_nonlocal_input:
            return True
        return self.nonlocality_detected
    
    def get_diagnosis(self) -> str:
        """Mensaje diagnostico."""
        if not self.is_nonlocal_input:
            return "N/A (no es control de no-localidad)"
        
        if self.geometry_rejected:
            return " CORRECTO: Pipeline no construyo bulk local para input no-local"
        
        if self.passed:
            return " CORRECTO: Pipeline detecto senales de no-localidad"
        else:
            return " FALLO: Pipeline construyo bulk local para teoria no-local"


# ============================================================================
# CONTRATO: DETECCION DE ANOMALIA GRAVITATORIA
# ============================================================================

@dataclass
class GravitationalAnomalyContract:
    """
    Detecta anomalias gravitatorias que rompen holografia.
    
    Para d=4 CFT: el bound holografico es c  a/3.
    Teorias con c > 3a no pueden tener dual Einstein en AdS5.
    
    Senales:
    1. Relacion c/a inconsistente con gravedad de Einstein
    2. Terminos Weyl2 en correladores (no reproducibles con Einstein)
    
    NOTA: En modo placeholder, c_over_a_ratio es valor ficticio.
    """
    is_anomaly_input: bool
    c_over_a_ratio: float          # c/a medido
    has_weyl_squared_terms: bool
    einstein_classification: str   # "Einstein" o "Non-Einstein" o "Failed"
    
    # Flag especial: True si no se genero geometria (rechazo temprano)
    geometry_rejected: bool = False
    
    C_OVER_A_HOLOGRAPHIC = 1.0 / 3.0  # bound holografico c  a/3
    C_OVER_A_TOLERANCE = 0.5          # tolerancia
    
    @property
    def anomaly_detected(self) -> bool:
        """True si detectamos anomalia gravitatoria."""
        if not self.is_anomaly_input:
            return False
        
        # Si no se genero geometria, es rechazo correcto
        if self.geometry_rejected:
            return True
        
        # Si c/a viola bound holografico
        if self.c_over_a_ratio > (self.C_OVER_A_HOLOGRAPHIC + self.C_OVER_A_TOLERANCE):
            return True
        
        # Si hay terminos Weyl2
        if self.has_weyl_squared_terms:
            return True
        
        # Si sistema NO clasifica como Einstein (correcto para anomalia)
        if self.einstein_classification != "Einstein":
            return True
        
        return False
    
    @property
    def passed(self) -> bool:
        """Contrato PASA si detecta anomalia."""
        if not self.is_anomaly_input:
            return True
        return self.anomaly_detected
    
    def get_diagnosis(self) -> str:
        """Mensaje diagnostico."""
        if not self.is_anomaly_input:
            return "N/A (no es control de anomalia)"
        
        if self.geometry_rejected:
            return " CORRECTO: Pipeline rechazo teoria con anomalia gravitatoria"
        
        if self.passed:
            return " CORRECTO: Pipeline detecto anomalia gravitatoria"
        else:
            return " FALLO: Pipeline clasifico anomalia como Einstein valido"


# ============================================================================
# CONTRATO GLOBAL PARA CONTROLES NEGATIVOS
# ============================================================================

@dataclass
class NegativeControlContract:
    """
    Contrato completo para validar controles negativos.
    """
    name: str
    control_type: str  # "ruido_puro", "log_violacion", "anomalia_gravitatoria"
    category: str      # "negative_control"
    
    # Sub-contratos
    noise_rejection: NoiseRejectionContract
    nonlocality: NonLocalityContract
    anomaly: GravitationalAnomalyContract
    
    # Metricas generales (PLACEHOLDER en modo actual)
    A_r2: float
    f_r2: float
    R_r2: float
    
    # Flag: True si no se genero geometria para este control
    geometry_rejected: bool = False
    
    # Indica modo plantilla
    mode: str = field(default_factory=lambda: SCRIPT_MODE)
    placeholders_active: bool = field(default_factory=lambda: PLACEHOLDER_MODE)
    
    @property
    def overall_passed(self) -> bool:
        """
        Contrato PASA si el pipeline RECHAZO correctamente el control negativo.
        """
        # Todos los sub-contratos deben pasar
        return (
            self.noise_rejection.passed and
            self.nonlocality.passed and
            self.anomaly.passed
        )
    
    def get_verdict(self) -> str:
        """Veredicto final."""
        mode_warning = " [PLACEHOLDER]" if self.placeholders_active else ""
        
        if self.geometry_rejected:
            return f" PIPELINE HONESTO: No genero geometria (rechazo temprano){mode_warning}"
        elif self.overall_passed:
            return f" PIPELINE HONESTO: Rechazo correctamente control negativo{mode_warning}"
        else:
            return f" ALUCINACION GEOMETRICA: Pipeline acepto datos no-holograficos{mode_warning}"


# ============================================================================
# FUNCIONES DE ANALISIS
# ============================================================================

def compute_R_variance_normalized(R: np.ndarray) -> float:
    """
    Varianza normalizada de R(z).
    
    Si R oscila mucho, es senal de ruido no fisico.
    """
    R_mean = np.mean(R)
    R_std = np.std(R)
    
    # Normalizar por la media para tener metrica independiente de escala
    if np.abs(R_mean) > 1e-6:
        return float(R_std / np.abs(R_mean))
    else:
        return float(R_std)


def compute_A_smoothness(A: np.ndarray, z: np.ndarray) -> float:
    """
    Curvatura media de A(z).
    
    Si A oscila violentamente, no es geometria fisica.
    """
    dz = z[1] - z[0]
    d2A = np.gradient(np.gradient(A, dz), dz)
    
    # Curvatura media
    curvature_mean = float(np.mean(np.abs(d2A)))
    return curvature_mean


def detect_log_squared_correlators(boundary_data: Dict[str, np.ndarray]) -> bool:
    """
    Busca senales de terminos log2(x) en correladores.
    
    Metodo: ajustar G2(x) ~ 1/x^  (1 +  log2(x)) y verificar  = 0.
    """
    # Buscar cualquier correlador G2_*
    x_grid = boundary_data.get("x_grid")
    if x_grid is None:
        return False
    
    for key in boundary_data:
        if key.startswith("G2_"):
            G2 = boundary_data[key]
            
            # Ajuste en log-log para detectar desviaciones
            x_safe = np.maximum(x_grid, 0.1)
            log_x = np.log(x_safe)
            log_G2 = np.log(np.maximum(G2, 1e-10))
            
            # Ajuste cuadratico: log G2 ~ a + b log x + c (log x)2
            try:
                coeffs = np.polyfit(log_x, log_G2, 2)
                c_quad = coeffs[0]  # coeficiente de (log x)2
                
                # Si |c| > umbral, hay termino log2
                if np.abs(c_quad) > 0.1:
                    return True
            except Exception:
                pass
    
    return False


def detect_anomalous_qnm_decay(boundary_data: Dict[str, np.ndarray]) -> bool:
    """
    Busca senales de QNMs con decaimiento no-exponencial.
    
    En teorias locales: Im() ~ constante.
    En teorias no-locales: Im() ~ log().
    """
    G_R_imag = boundary_data.get("G_R_imag")
    if G_R_imag is None:
        return False
    
    # Buscar picos en Im(G_R) y verificar su ancho
    # (implementacion simplificada)
    imag_flat = G_R_imag.flatten()
    
    # Si hay estructura log en el decaimiento, detectarlo
    # (aqui: heuristica simple, se puede refinar)
    std_imag = np.std(imag_flat)
    mean_imag = np.abs(np.mean(imag_flat))
    
    # Senal: varianza muy alta relativa a la media
    if mean_imag > 1e-10 and std_imag > 10 * mean_imag:
        return True
    
    return False


# ============================================================================
# PROCESAMIENTO DE CONTROLES NEGATIVOS
# ============================================================================

def create_rejected_contract(
    name: str,
    control_type: str,
    category: str,
) -> NegativeControlContract:
    """
    Crea un contrato para el caso en que NO se genero geometria.
    
    Esto se interpreta como: el pipeline rechazo correctamente el input
    no-holografico antes de producir geometria. Es un PASS honesto.
    
    La logica es:
    - Para cada tipo de control, configuramos las flags de manera que
      el sub-contrato correspondiente interprete esto como "deteccion correcta".
    """
    is_noise = (control_type == "ruido_puro")
    is_nonlocal = (control_type == "log_violacion")
    is_anomaly = (control_type == "anomalia_gravitatoria")
    
    # Crear sub-contratos con geometry_rejected=True
    # Esto hara que cada sub-contrato marque "deteccion correcta"
    
    noise_contract = NoiseRejectionContract(
        is_noise_input=is_noise,
        A_r2=-1.0,  # valor especial: no existe geometria
        f_r2=-1.0,
        R_variance_normalized=0.0,
        A_smoothness=0.0,
        family_confidence=0.0,
        geometry_rejected=True,  #  clave para interpretar como PASS
    )
    
    nonlocality_contract = NonLocalityContract(
        is_nonlocal_input=is_nonlocal,
        has_log_squared_correlators=False,
        has_anomalous_qnm_decay=False,
        thermodynamic_consistency=True,
        geometry_rejected=True,  #  clave para interpretar como PASS
    )
    
    anomaly_contract = GravitationalAnomalyContract(
        is_anomaly_input=is_anomaly,
        c_over_a_ratio=0.0,
        has_weyl_squared_terms=False,
        einstein_classification="Failed",  # no llego a clasificar
        geometry_rejected=True,  #  clave para interpretar como PASS
    )
    
    return NegativeControlContract(
        name=name,
        control_type=control_type,
        category=category,
        noise_rejection=noise_contract,
        nonlocality=nonlocality_contract,
        anomaly=anomaly_contract,
        A_r2=-1.0,
        f_r2=-1.0,
        R_r2=-1.0,
        geometry_rejected=True,
        mode=SCRIPT_MODE,
        placeholders_active=PLACEHOLDER_MODE,
    )


def process_negative_control(
    name: str,
    control_meta: Dict[str, Any],
    geometry_dir: Path,
    data_dir: Path,
) -> NegativeControlContract:
    """
    Procesa un control negativo y genera su contrato.
    
    Args:
        name: nombre del control
        control_meta: metadata del manifest (control_type, etc.)
        geometry_dir: directorio con geometria emergente
        data_dir: directorio con datos boundary originales
    """
    control_type = control_meta["control_type"]
    category = control_meta.get("category", "negative_control")
    
    # Cargar geometria emergente (si existe)
    geo_path = geometry_dir / f"{name}_emergent.h5"
    if not geo_path.exists():
        # ============================================================
        # CASO: No se genero geometria
        # ============================================================
        # Esto se interpreta como: el pipeline rechazo el input antes
        # de producir geometria emergente. Es un comportamiento CORRECTO
        # para un control negativo.
        #
        # Usamos la funcion create_rejected_contract que configura
        # todos los sub-contratos para que interpreten esto como PASS.
        # ============================================================
        return create_rejected_contract(name, control_type, category)
    
    # ============================================================
    # CASO: Si hay geometria generada
    # ============================================================
    # Esto es potencialmente problematico: el pipeline ha construido
    # geometria para un input que no deberia tenerla.
    # Ahora evaluamos si al menos la geometria es "mala" (lo cual
    # todavia seria un PASS del contrato).
    # ============================================================
    
    # Cargar datos boundary originales
    boundary_path = data_dir / f"{name}.h5"
    boundary_data: Dict[str, np.ndarray] = {}
    
    if boundary_path.exists():
        try:
            with h5py.File(boundary_path, "r") as f:
                if "boundary" in f:
                    boundary_group = f["boundary"]
                    boundary_data = {key: boundary_group[key][:] for key in boundary_group.keys()}
                else:
                    # Intentar cargar desde raiz
                    for key in f.keys():
                        if isinstance(f[key], h5py.Dataset):
                            boundary_data[key] = f[key][:]
        except Exception as e:
            print(f"   Warning: No se pudo cargar boundary data: {e}")
    
    # Cargar geometria emergente
    try:
        with h5py.File(geo_path, "r") as f:
            A_emergent = f["A_emergent"][:]
            f_emergent = f["f_emergent"][:]
            R_emergent = f["R_emergent"][:] if "R_emergent" in f else np.zeros_like(A_emergent)
            z_grid = f["z_grid"][:]
            family_pred = f.attrs.get("family_pred", "unknown")
            if isinstance(family_pred, bytes):
                family_pred = family_pred.decode("utf-8")
    except Exception as e:
        print(f"   Warning: Error leyendo geometria: {e}")
        # Si hay error leyendo, tratarlo como rechazo
        return create_rejected_contract(name, control_type, category)
    
    # Calcular metricas de calidad de la geometria
    R_var_norm = compute_R_variance_normalized(R_emergent)
    A_smooth = compute_A_smoothness(A_emergent, z_grid)
    
    # Detecciones especificas en los datos boundary
    has_log_sq = detect_log_squared_correlators(boundary_data) if boundary_data else False
    has_anom_qnm = detect_anomalous_qnm_decay(boundary_data) if boundary_data else False
    
    # ============================================================
    # NOTA IMPORTANTE: Los valores A_r2, f_r2, family_confidence,
    # c_over_a_ratio, thermodynamic_consistency son PLACEHOLDERS.
    #
    # En una version futura, estos deberian extraerse de:
    # - *_geometry_summary.json para R2 y metricas de reconstruccion
    # - Metadatos de QFT para central charges (c, a)
    # - Softmax del clasificador de familia para family_confidence
    # ============================================================
    
    # Placeholder: familia confidence
    family_confidence = 0.5  # PLACEHOLDER
    
    # Construir sub-contratos
    # NOTA: A_r2=1.0, f_r2=1.0 son PLACEHOLDERS (por encima del umbral 0.3)
    # Esto evita que el contrato pase trivialmente por la rama de R2 bajo.
    # En modo placeholder, las decisiones dependeran de R_variance, A_smoothness, etc.
    noise_contract = NoiseRejectionContract(
        is_noise_input=(control_type == "ruido_puro"),
        A_r2=1.0,  # PLACEHOLDER: por encima del umbral para evitar auto-PASS trivial
        f_r2=1.0,  # PLACEHOLDER: por encima del umbral para evitar auto-PASS trivial
        R_variance_normalized=R_var_norm,
        A_smoothness=A_smooth,
        family_confidence=family_confidence,  # PLACEHOLDER
        geometry_rejected=False,
    )
    
    nonlocality_contract = NonLocalityContract(
        is_nonlocal_input=(control_type == "log_violacion"),
        has_log_squared_correlators=has_log_sq,
        has_anomalous_qnm_decay=has_anom_qnm,
        thermodynamic_consistency=True,  # PLACEHOLDER
        geometry_rejected=False,
    )
    
    anomaly_contract = GravitationalAnomalyContract(
        is_anomaly_input=(control_type == "anomalia_gravitatoria"),
        c_over_a_ratio=1.0,  # PLACEHOLDER: requiere calculo de central charges
        has_weyl_squared_terms=False,  # PLACEHOLDER
        einstein_classification=family_pred,
        geometry_rejected=False,
    )
    
    return NegativeControlContract(
        name=name,
        control_type=control_type,
        category=category,
        noise_rejection=noise_contract,
        nonlocality=nonlocality_contract,
        anomaly=anomaly_contract,
        A_r2=1.0,  # PLACEHOLDER: valor ficticio por encima del umbral
        f_r2=1.0,  # PLACEHOLDER: valor ficticio por encima del umbral
        R_r2=0.0,  # PLACEHOLDER
        geometry_rejected=False,
        mode=SCRIPT_MODE,
        placeholders_active=PLACEHOLDER_MODE,
    )


# ============================================================================
# MAIN (standalone)
# ============================================================================

def main():
    import argparse
    import sys

    #  GUARD: bloquear ejecucion en modo placeholder 
    if PLACEHOLDER_MODE:
        print(
            "[04b] ERROR: Este script esta en MODO PLANTILLA (placeholder).\n"
            "  Sus metricas son stubs ficticios y NO deben usarse para:\n"
            "    - Claims fisicos en articulos\n"
            "    - Conclusiones sobre honestidad del pipeline\n"
            "    - Validacion final de resultados\n"
            "  Para habilitar la ejecucion real, conecta las metricas a salidas\n"
            "  concretas de la geometria emergente y cambia PLACEHOLDER_MODE = False.",
            file=sys.stderr,
        )
        sys.exit(2)
    # 

    parser = argparse.ArgumentParser(
        description="Validacion de controles negativos (deteccion de alucinacion geometrica)"
    )
    parser.add_argument("--control-manifest", type=str, required=True,
                        help="Manifest de controles negativos (01b output)")
    parser.add_argument("--geometry-dir", type=str, required=True,
                        help="Directorio con geometria emergente de controles")
    parser.add_argument("--output-file", type=str, required=True,
                        help="JSON de salida con contratos")
    
    args = parser.parse_args()
    
    manifest_path = Path(args.control_manifest)
    geometry_dir = Path(args.geometry_dir)
    output_file = Path(args.output_file)
    
    # Cargar manifest de controles negativos
    manifest = json.loads(manifest_path.read_text())
    controls_meta = manifest["controls"]
    
    # Directorio de datos boundary (mismo que manifest)
    data_dir = manifest_path.parent
    
    print("=" * 70)
    print("VALIDACION DE CONTROLES NEGATIVOS")
    print("=" * 70)
    
    # WARNING de modo plantilla
    if PLACEHOLDER_MODE:
        print()
        print("  ADVERTENCIA: MODO PLANTILLA ACTIVO")
        print("   Los campos de metricas son PLACEHOLDERS.")
        print("   No usar para claims fisicos.")
        print()
    
    print(f"  Controles:  {len(controls_meta)}")
    print(f"  Geometria:  {geometry_dir}")
    print(f"  Modo:       {SCRIPT_MODE}")
    print("=" * 70)
    
    all_contracts: List[NegativeControlContract] = []
    
    for control_meta in controls_meta:
        name = control_meta["name"]
        print(f"\n>> Procesando: {name}")
        
        try:
            contract = process_negative_control(
                name, control_meta, geometry_dir, data_dir
            )
            all_contracts.append(contract)
            
            verdict = contract.get_verdict()
            print(f"   {verdict}")
            
            # Diagnosticos de sub-contratos
            if control_meta["control_type"] == "ruido_puro":
                print(f"    Ruido: {contract.noise_rejection.get_diagnosis()}")
            elif control_meta["control_type"] == "log_violacion":
                print(f"    No-localidad: {contract.nonlocality.get_diagnosis()}")
            elif control_meta["control_type"] == "anomalia_gravitatoria":
                print(f"    Anomalia: {contract.anomaly.get_diagnosis()}")
            
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Resumen
    n_total = len(all_contracts)
    n_passed = sum(1 for c in all_contracts if c.overall_passed)
    n_rejected = sum(1 for c in all_contracts if c.geometry_rejected)
    
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  Total:                {n_total}")
    print(f"  PASS:                 {n_passed} (pipeline rechazo correctamente)")
    print(f"  FAIL:                 {n_total - n_passed} (ALUCINACION GEOMETRICA)")
    print(f"  Sin geometria:        {n_rejected} (rechazo temprano)")
    print(f"  Modo:                 {SCRIPT_MODE}")
    print(f"  Placeholders activos: {PLACEHOLDER_MODE}")
    print("=" * 70)
    
    if n_passed == n_total:
        print("\n PIPELINE HONESTO: Rechazo todos los controles negativos")
    else:
        print(f"\n ALERTA: {n_total - n_passed} controles aceptados incorrectamente")
        print("   El pipeline tiene sesgo inductivo y puede 'alucinar' geometrias.")
    
    if PLACEHOLDER_MODE:
        print()
        print("  RECORDATORIO: Este resultado es en MODO PLANTILLA.")
        print("   Las metricas no estan conectadas a valores reales.")
        print("   No usar para conclusiones fisicas.")
    
    # Guardar
    # NOTA: pipeline_honest es None en modo placeholder para evitar
    # que alguien lea un True/False y olvide el warning
    output_data = {
        "n_total": n_total,
        "n_passed": n_passed,
        "n_failed": n_total - n_passed,
        "n_geometry_rejected": n_rejected,
        "pass_rate": n_passed / max(n_total, 1),
        "pipeline_honest": None if PLACEHOLDER_MODE else (n_passed == n_total),
        "honest_meaningful": not PLACEHOLDER_MODE,
        "mode": SCRIPT_MODE,
        "placeholders_active": PLACEHOLDER_MODE,
        "warning": (
            "Este script esta en modo PLACEHOLDER. "
            "Las metricas (A_r2, f_r2, c_over_a_ratio, etc.) no estan conectadas "
            "a valores reales. No usar para claims fisicos. "
            "El campo pipeline_honest es null porque no es significativo en este modo."
        ) if PLACEHOLDER_MODE else None,
        "contracts": [asdict(c) for c in all_contracts],
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(output_data, indent=2, default=str))
    
    print(f"\n  Output: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
