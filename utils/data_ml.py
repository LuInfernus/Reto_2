# # Permite la asignación el cálculo de riesgo financiero para el modelo

import pandas as pd
import numpy as np

# 1) Cargar
df = pd.read_csv("data/df_financiero.csv")

# 2) Pesos (suman 1.0) según pdf de ejemplo
# se puede ajustar dependisndo los requerimeintos
pesos = {
    'flujo_caja_promedio': 0.20,  
    'nivel_endeudamiento': 0.10,    
    'variabilidad_ingresos': 0.10,   
    'liquidez_corriente': 0.10,   
    'margen_operativo': 0.10,      
    'cobertura_interes': 0.10,    
    'roe': 0.15,                   
    'roa': 0.15                   
}

cols_mejor = ['flujo_caja_promedio','liquidez_corriente','margen_operativo','cobertura_interes','roe','roa']
cols_peor  = ['nivel_endeudamiento','variabilidad_ingresos'] 

# 3) Normalización robusta (percentiles) para evitar outliers aplastando todo
dfn = df.copy()
for col in pesos.keys():
    lo = df[col].quantile(0.05)   # 5%
    hi = df[col].quantile(0.95)   # 95%
    if lo == hi:
        # si es constante, marca como NaN para luego quitar su peso
        dfn[col] = np.nan
    else:
        x = df[col].clip(lo, hi)
        dfn[col] = (x - lo) / (hi - lo)

# 4)  “de costo”
for col in cols_peor:
    if col in dfn.columns:
        dfn[col] = 1.0 - dfn[col]

# 5) Reajustar pesos si alguna columna quedó NaN (constante)
pesos_validos = {c:w for c,w in pesos.items() if c in dfn.columns and not dfn[c].isna().all()}
suma = sum(pesos_validos.values())
pesos_validos = {c:w/suma for c,w in pesos_validos.items()}  # renormalizar a 1

# 6) Score ponderado
dfn['score_final'] = 0.0
for col, w in pesos_validos.items():
    dfn['score_final'] += dfn[col].fillna(0) * w  # NaN -> 0 contribución

# 7) Umbrales cuantiles: se procede con el uso de los cuartiles 80 y 60 para tener un margen de referencia

q60 = dfn['score_final'].quantile(0.60)
q80 = dfn['score_final'].quantile(0.80)
def clasificar(score):
    if score >= q80: return 0
    elif score >= q60: return 1
    else: return 2

dfn['riesgo'] = dfn['score_final'].apply(clasificar)

# Diagnóstico rápido
print(dfn['riesgo'].value_counts().sort_index())
print(dfn['score_final'].describe())

# 8) Guardar
dfn.to_csv("data/df_score.csv", index=False)

