# Nodelo de clasificación para generar los pesos y predicir el riesgo de futuras empresas

# -*- coding: utf-8 -*-
import os, json
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
import joblib

# 1) Configuración
INPUT_CSV = "data/df_score.csv"
OUTPUT_DIR = "models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2) Cargar data y crear data para uso fuera y preparar X, y
df = pd.read_csv(INPUT_CSV)

df = df.dropna()
df = df.drop(columns=["score_final", "expediente"])

df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

# Partir
n_test = int(len(df) * 0.05)
df_test  = df.iloc[:n_test].copy()
df_train = df.iloc[n_test:].copy()

df_test.iloc[:, :-1].to_csv("data/df_pruebas.csv", index=False)

X = df_train.drop(columns=["riesgo"])
y = df_train["riesgo"].astype(int)

# Guardar orden exacto de columnas para inferencia
feature_cols = list(X.columns)
with open(os.path.join(OUTPUT_DIR, "feature_columns.json"), "w", encoding="utf-8") as f:
    json.dump(feature_cols, f, ensure_ascii=False, indent=2)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Escalado (necesario para SVM)
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

joblib.dump(scaler, os.path.join(OUTPUT_DIR, "scaler.joblib"))

# Modelo SVM multiclase
clf = SVC(kernel="rbf", C=1.0, gamma="scale", probability=False, random_state=42)
clf.fit(X_train_sc, y_train)

# Evaluación
y_pred = clf.predict(X_test_sc)
# print("\n=== Evaluación (Test) ===")
# print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
# print(f"F1-macro: {f1_score(y_test, y_pred, average='macro'):.4f}")
# print("Matriz de confusión:")
# print(confusion_matrix(y_test, y_pred))
# print("\nReporte de clasificación:")
# print(classification_report(y_test, y_pred, digits=4))

# Guardar modelo
joblib.dump(clf, os.path.join(OUTPUT_DIR, "modelo_svm.joblib"))

# print("\nArtefactos guardados en:", OUTPUT_DIR)
# print("- modelo_svm.joblib")
# print("- scaler.joblib")
# print("- feature_columns.json")