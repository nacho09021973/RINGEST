import h5py
import pandas as pd
import yaml
import numpy as np
from pathlib import Path

file_path = Path('IGWN-GWTC4p0-0f954158d_720-PESummaryTable.hdf5')

with h5py.File(file_path, 'r') as f:
    data = f['summary_info'][:]

df = pd.DataFrame(data)

# Decodificar strings
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].apply(lambda x: x.decode('utf-8').strip() if isinstance(x, bytes) else x)

# Columnas importantes
df = df[['gw_name', 'result_label',
         'final_mass_source_median',
         'final_mass_source_lower',
         'final_mass_source_upper',
         'final_spin_median',
         'final_spin_lower',
         'final_spin_upper']].copy()

df = df[np.isfinite(df['final_mass_source_median']) & 
        np.isfinite(df['final_spin_median'])].reset_index(drop=True)

# === CORRECCION DE SIGMAS (siempre positivos) ===
df['sigma_M_final_Msun'] = np.abs(df['final_mass_source_upper'] - df['final_mass_source_lower']) / 2
df['sigma_chi_final']     = np.abs(df['final_spin_upper']     - df['final_spin_lower'])     / 2

# === LIMPIEZA de nombres de analisis ===
def clean_method(label):
    if 'SEOBNRv5PHM' in label:
        return 'pSEOBNRv5PHM'
    elif 'IMRPhenomXPHM' in label or 'IMRPhenomX' in label:
        return 'IMRPhenomXPHM'
    elif 'NRSur7dq4' in label:
        return 'NRSur7dq4'
    elif 'Mixed' in label:
        return 'Mixed'
    elif 'IMRPhenomNSBH' in label:
        return 'IMRPhenomNSBH'
    else:
        return label[:50]  # fallback corto

df['analysis_method'] = df['result_label'].apply(clean_method)

# === GENERAR YAML ===
yaml_list = []
for event, group in df.groupby('gw_name'):
    for _, row in group.iterrows():
        entry = {
            'event': event,
            'ifo': 'null',
            'M_final_Msun': round(float(row['final_mass_source_median']), 2),
            'sigma_M_final_Msun': round(float(row['sigma_M_final_Msun']), 2),
            'chi_final': round(float(row['final_spin_median']), 3),
            'sigma_chi_final': round(float(row['sigma_chi_final']), 3),
            'source_kind': 'data_release',
            'analysis_method': row['analysis_method'],
            'detector_set': 'null',
            'credible_interval': '90%',
            'modes': [{
                'l': 2, 'm': 2, 'n': 0,
                'f_hz': None, 'sigma_f_hz': None,
                'tau_ms': None, 'sigma_tau_ms': None,
                'source_paper': 'GWTC-4.0 Parameter Estimation data release',
                'source_doi': '10.5281/zenodo.16053484',
                'source_url': 'https://zenodo.org/records/16053484',
                'source_locator': 'PESummaryTable summary_info',
                'notes': f'sigma from 90% CI; analysis: {row["result_label"]}'
            }]
        }
        yaml_list.append(entry)

with open('GWTC4_remnant_params_FIXED.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(yaml_list, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f'Listo! Se generaron {len(yaml_list)} entradas en GWTC4_remnant_params_FIXED.yaml')
print(' Sigmas siempre positivos y nombres de analisis limpios')