# FILTRACIÓN DE DATA PARA OBTENER LA DATA INICIAL

import pandas as pd
import numpy as np

# 1) Cargar dataset base
df = pd.read_csv("data/bi_ranking.csv")

# filtramos por el anio 2024
df = df[df['anio'] == 2024]

# filtramos pymes 

'''
CODIGO ORGANICO DE LA PRODUCCION, COMERCIO E INVERSIONES, COPCI
Art. 53.- Definición y Clasificación de las MIPYMES.- La Micro, Pequeña y Mediana empresa es toda
persona natural o jurídica que, como una unidad productiva, ejerce una actividad de producción,
comercio y/o servicios, y que cumple con el número de trabajadores y valor bruto de las ventas
anuales, señalados para cada categoría, de conformidad con los rangos que se establecerán en el
reglamento de este Código.
En caso de inconformidad de las variables aplicadas, el valor bruto de las ventas anuales
prevalecerá sobre el número de trabajadores, para efectos de determinar la categoría de una
empresa. Los artesanos que califiquen al criterio de micro, pequeña y mediana empresa recibirán los
beneficios de este Código, previo cumplimiento de los requerimientos y condiciones señaladas en el
reglamento.

REGLAMENTO DE INVERSIONES DEL CODIGO ORGANICO DE LA PRODUCCION

Art. 106.- Clasificación de las MYPIMES.- Para la definición de los programas de fomento y
desarrollo empresarial a favor de las micro, pequeñas y medianas empresas, estas se considerarán
de acuerdo a las categorías siguientes:
a.- Micro empresa: Es aquella unidad productiva que tiene entre 1 a 9 trabajadores y un valor de
ventas o ingresos brutos anuales iguales o menores de trescientos mil (US $ 300.000,00) dólares de
los Estados Unidos de América;
b.- Pequeña empresa: Es aquella unidad de producción que tiene de 10 a 49 trabajadores y un valor
de ventas o ingresos brutos anuales entre trescientos mil uno (US $ 300.001,00) y un millón (US $
1000.000,00) de dólares de los Estados Unidos de América; y,
c.- Mediana empresa: Es aquella unidad de producción que tiene de 50 a 199 trabajadores y un valor
de ventas o ingresos brutos anuales entre un millón uno (USD 1.000.001,00) y cinco millones (USD
5000.000,00) de dólares de los Estados Unidos de América.
'''

df = df[(df['n_empleados'] <= 199) & (df['ingresos_ventas'] <= 5_000_000)]

# 2) Construir las variables financieras
df_financiero = pd.DataFrame()

df_financiero['expediente'] = df['expediente']

# Flujo de caja promedio (estimado): ingresos_totales - total_gastos
df_financiero['flujo_caja_promedio'] =round(df['ingresos_totales'] - df['total_gastos'],2)

# Nivel de endeudamiento: deuda_total / activos (con división segura)
den = df['activos'].replace(0, np.nan)
df_financiero['nivel_endeudamiento'] = df['deuda_total'] / den

# Variabilidad en ingresos (proxy rápido sin series temporales): z-score de ingresos_ventas
mu = df['ingresos_ventas'].mean()
sigma = df['ingresos_ventas'].std(ddof=0)
if sigma == 0 or np.isnan(sigma):
    # si no hay variación, poner 0
    df_financiero['variabilidad_ingresos'] = 0.0
else:
    df_financiero['variabilidad_ingresos'] = (df['ingresos_ventas'] - mu) / sigma

# Liquidez y eficiencia
df_financiero['liquidez_corriente'] = df['liquidez_corriente']
df_financiero['margen_operativo'] = df['margen_operacional']
df_financiero['cobertura_interes'] = df['cobertura_interes']
df_financiero['roe'] = df['roe']
df_financiero['roa'] = df['roa']

# 3) Limpiar infinitos y NaN que pudieran quedar por divisiones
df_financiero = df_financiero.replace([np.inf, -np.inf], np.nan)
df_financiero = df_financiero.dropna()

# df_financiero['nivel_endeudamiento'] = df_financiero['nivel_endeudamiento'].fillna(-1)

# 4) Guardar a CSV
ruta_salida = "data/df_financiero.csv"  # guarda en el directorio de trabajo actual
df_financiero.to_csv(ruta_salida, index=False)

# print("Archivo generado:", ruta_salida)
# print(df_financiero.head())
# print(df_financiero.info())