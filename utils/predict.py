# fichero para probar como se comporta el modelo 

# predict_model.py
import pandas as pd
import joblib
import json

# 1) Configuración de rutas
MODEL_PATH = "models/modelo_svm.joblib"  # Cambia a models_svm.joblib si usas SVM
FEATURES_PATH = "models/feature_columns.json"
DATA_PATH = "data/df_pruebas.csv"       # Archivo de pruebas sin etiquetas
OUTPUT_PATH = "data/predicciones.csv"

# 2) Cargar el modelo y la lista de columnas de features
clf = joblib.load(MODEL_PATH)
with open(FEATURES_PATH, "r", encoding="utf-8") as f:
    feature_cols = json.load(f)

# 3) Cargar el archivo de pruebas y reordenar columnas
X_new = pd.read_csv(DATA_PATH)
X_new = X_new[feature_cols]

# 4) Si el modelo necesita escalado (solo en SVM), aplicar scaler
try:
    scaler = joblib.load("models/scaler.joblib")
    X_new = scaler.transform(X_new)
except FileNotFoundError:
    pass  # Si no existe scaler, significa que el modelo no lo requiere

# 5) Generar predicciones
pred = clf.predict(X_new)

# 6) Mapear etiquetas numéricas a texto
mapa = {0: "Bajo", 1: "Medio", 2: "Alto"}
pred_texto = [mapa.get(int(p), "Desconocido") for p in pred]

# 7) Guardar resultados en un CSV
out = pd.DataFrame({
    "pred_num": pred,
    "pred_texto": pred_texto
})
out.to_csv(OUTPUT_PATH, index=False)

print(f"Predicciones guardadas en: {OUTPUT_PATH}")
