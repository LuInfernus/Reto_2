# Informe Técnico — Scoring Alternativo PYMEs

## 1. Objetivo
Evaluar riesgo financiero y/o confianza crediticia de PYMEs integrando **datos tradicionales** y **no tradicionales**.

## 2. Datos
- Financieros: flujo de caja, endeudamiento, variabilidad, pagos, entregas, margen, liquidez.
- No tradicionales: reputación digital (reseñas), actividad en redes, referencias con proveedores.
- Opcional: scraping desde URL pública (demo).

## 3. Preprocesamiento
- Normalización a [0,1] (heurística: min–max por campo).
- Sentimiento NLP para reseñas: `transformers` si disponible; `nlp.py` (léxico) como fallback.
- Construcción de vector de características alineado con `weights/matriz_riesgo.yaml`.

## 4. Modelo de Scoring
- **Suma ponderada** de contribuciones: `score = Σ feature_i * peso_i`.
- **Clasificación** por umbrales (configurable): Bajo/Medio/Alto riesgo (o Confianza Alta/Moderada/Baja).
- Justificación: se entrega tabla de contribuciones y top factores.

> Este POC es **interpretable** y configurable. En producción se puede:
> - Entrenar un **RandomForest/GBM** para aprender pesos y no-linealidades.
> - Añadir **SHAP** para explicabilidad por instancia.
> - Afinar umbrales por **curvas ROC/PR** vs. default histórico.

## 5. Simulaciones
- **+10% ingresos** (`escenario_ingresos`): impacto directo en contribución correspondiente.
- **+0.1 reputación** (`reputacion_digital`): impacto directo y re-clasificación potencial.
- Sliders en UI (futuros): variar 0–1 y recomputar.

## 6. Métricas y Validación (propuesta)
- Si se dispone de etiquetas (default/no default): AUC, KS, Gini, Brier, matriz de confusión por bandas.
- Validación por sector/segmento.
- **Backtesting** con ventanas temporales.

## 7. Ética y Cumplimiento
- Riesgos de sesgo: reseñas sesgadas, ataques de reputación.
- Medidas: auditoría, listas de control, límites de importancia de variables no tradicionales, explicabilidad.

## 8. Despliegue
- Flask + WSGI (gunicorn) o contenedor Docker.
- Cache de modelos NLP.
- Endpoints API (futuros): `/api/score`, `/api/simulate`.

## 9. Limitaciones
- Scraping real depende de TOS de cada plataforma.
- NLP sin fine-tuning local.
- Pesos iniciales basados en matriz de ejemplo (no calibrados con defaults reales).
