import h5py
import pandas as pd
import yaml
import numpy as np
from pathlib import Path

file_path = Path('IGWN-GWTC4p0-0f954158d_720-PESummaryTable.hdf5')  # cambia la ruta si hace falta

with h5py.File(file_path, 'r') as f:
    data = f['summary_info'][:]

df = pd.DataFrame(data)

# Decodificar columnas de bytes
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].apply(lambda x: x.decode('utf-8', errors='ignore').strip() if isinstance(x, bytes) else x)

# Columnas relevantes
df = df[['gw_name', 'result_label',
         'final_mass_source_median', 'final_mass_source_lower', 'final_mass_source_upper',
         'final_spin_median', 'final_spin_lower', 'final_spin_upper']].copy()

# Filtrar filas validas
df = df[np.isfinite(df['final_mass_source_median']) & np.isfinite(df['final_spin_median'])].reset_index(drop=True)

# Sigma aproximado (como hacias tu)
df['sigma_M_final_Msun'] = (df['final_mass_source_upper'] - df['final_mass_source_lower']) / 2
df['sigma_chi_final'] = (df['final_spin_upper'] - df['final_spin_lower']) / 2

yaml_list = []
for event, group in df.groupby('gw_name'):
    for _, row in group.iterrows():
        analysis = row['result_label']
        # Mapeo a tu estilo de nombres
        if 'SEOBNRv5PHM' in analysis:
            method = 'pSEOBNRv5PHM'
        elif 'IMRPhenomX' in analysis:
            method = 'IMRPhenomXPHM'
        elif 'NRSur7dq4' in analysis:
            method = 'NRSur7dq4'
        elif 'Mixed' in analysis:
            method = 'Mixed'
        else:
            method = analysis[:40]

        entry = {
            'event': event,
            'ifo': 'null',
            'M_final_Msun': round(float(row['final_mass_source_median']), 2),
            'sigma_M_final_Msun': round(float(row['sigma_M_final_Msun']), 2),
            'chi_final': round(float(row['final_spin_median']), 3),
            'sigma_chi_final': round(float(row['sigma_chi_final']), 3),
            'source_kind': 'data_release',
            'analysis_method': method,
            'detector_set': 'null',
            'credible_interval': '90%',
            'modes': [{
                'l': 2,
                'm': 2,
                'n': 0,
                'f_hz': None,
                'sigma_f_hz': None,
                'tau_ms': None,
                'sigma_tau_ms': None,
                'source_paper': 'GWTC-4.0 Parameter Estimation data release',
                'source_doi': '10.5281/zenodo.16053484',
                'source_url': 'https://zenodo.org/records/16053484',
                'source_locator': 'PESummaryTable summary_info',
                'notes': f'sigma approximated from asymmetric 90% CI; analysis: {analysis}; ringdown f/tau not in this summary table'
            }]
        }
        yaml_list.append(entry)

# Guardar el YAML completo
with open('GWTC4_remnant_params.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(yaml_list, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f'Listo! Se generaron {len(yaml_list)} entradas en GWTC4_remnant_params.yaml')