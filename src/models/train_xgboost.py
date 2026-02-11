"""
Treinamento do modelo XGBoost do projeto ARIS.

Este script:
- Utiliza dados clínicos extraídos de espelhos de regulação
- Combina regras clínicas (flags tabulares) com NLP (TF-IDF)
- Treina um modelo supervisionado com target heurístico (EXPERIMENTAL)

IMPORTANTE:
Este target é TEMPORÁRIO e serve apenas para validação técnica
do pipeline de ML. NÃO representa decisão clínica real.
"""

import os
import numpy as np
import pandas as pd
import joblib

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from src.features.text_vectorization import vectorize_text
from src.features.feature_builder import FeatureBuilder

import inspect
from src.features import text_vectorization

print(
    "📂 Arquivo de vetorização carregado:",
    inspect.getfile(text_vectorization)
)

# =============================================================================
# CONFIGURAÇÕES DE CAMINHO
# =============================================================================

PROCESSED_DATA_PATH = "data/processed/dataset_espelhos.csv"
MODEL_OUTPUT_PATH = "models/xgboost_model.json"
VECTORIZER_PATH = "models/vectorizers/tfidf_vectorizer.pkl"

# =============================================================================
# TARGET HEURÍSTICO — MODO EXPERIMENTAL
# =============================================================================


def gerar_target_simulado(row):
    """
    TARGET EXPERIMENTAL (modo debug técnico).

    Estratégia:
    - Criar variabilidade (0 e 1)
    - Refletir "caso clínico relevante" de forma ampla
    - Permitir treino, predição e inspeção do modelo

    ⚠️ NÃO É PROTOCOLO CLÍNICO
    """

    # 1. Indício direto de gastro
    if row.get("Sinais_Gastro_Hepato", 0) == 1:
        return 1

    # 2. Situações clínicas relevantes (proxy)
    if (
        row.get("Hemorragia_Ativa", 0) == 1
        or row.get("Suspeita_Infecciosa", 0) == 1
    ):
        return 1

    # 3. Adulto internado com evolução registrada (sinal fraco, mas útil)
    try:
        if (
            pd.notna(row.get("Idade"))
            and row.get("Idade", 0) >= 40
        ):
            return 1
    except Exception:
        pass

    return 0


# =============================================================================
# PIPELINE DE TREINAMENTO
# =============================================================================


def train_model():
    print("🚀 Iniciando treinamento do modelo ARIS (XGBoost)...")

    # -------------------------------------------------------------------------
    # 1. CARREGAMENTO DOS DADOS
    # -------------------------------------------------------------------------
    if not os.path.exists(PROCESSED_DATA_PATH):
        print(f"❌ Arquivo não encontrado: {PROCESSED_DATA_PATH}")
        print("👉 Execute o pipeline de ingestão antes do treino.")
        return

    df = pd.read_csv(PROCESSED_DATA_PATH)
    print(f"📊 Registros carregados: {df.shape[0]}")

    # -------------------------------------------------------------------------
    # 2. GERAÇÃO DO TARGET (EXPERIMENTAL)
    # -------------------------------------------------------------------------
    print("🎯 Gerando target heurístico EXPERIMENTAL...")
    df["Target"] = df.apply(gerar_target_simulado, axis=1)

    print("⚖️ Distribuição das classes:")
    print(df["Target"].value_counts())

    # -------------------------------------------------------------------------
    # 3. VETORIZAÇÃO DOS TEXTOS CLÍNICOS (NLP)
    # -------------------------------------------------------------------------
    print("🔠 Vetorizando textos clínicos com TF-IDF...")

    TEXT_COLUMNS = [
        "Justificativa_Internacao",
        "Evolucao",
        "Sinais_Vitais_Texto",
    ]

    df_nlp, vectorizer = vectorize_text(
        df,
        text_columns=TEXT_COLUMNS,
        max_features=300,
    )

    if vectorizer is None:
        print("❌ Falha na vetorização (textos vazios). Abortando treino.")
        return

    os.makedirs(os.path.dirname(VECTORIZER_PATH), exist_ok=True)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"💾 Vetorizador salvo em: {VECTORIZER_PATH}")

    # -------------------------------------------------------------------------
    # 4. FEATURE BUILDER
    # -------------------------------------------------------------------------
    print("🔧 Aplicando FeatureBuilder (limpeza e validação final)...")

    builder = FeatureBuilder()
    df_final = builder.transform(df_nlp)

    if "Idade" in df_final.columns:
        nulos_idade = df_final["Idade"].isna().sum()
        if nulos_idade > 0:
            print(f"⚠️ {nulos_idade} registros com Idade inválida (NaN).")

    # -------------------------------------------------------------------------
    # 5. MATRIZ DE TREINO (FILTRAGEM FINAL)
    # -------------------------------------------------------------------------
    print("🧱 Preparando matriz de treino...")

    y = df_final["Target"]

    X = (
        df_final
        .drop(columns=["Target"])
        .select_dtypes(include=["number", "bool"])
    )

    print(f"🧹 Features finais para treino: {X.shape[1]} colunas numéricas")

    if y.nunique() < 2:
        raise ValueError(
            "❌ Target ainda degenerado. "
            "Mesmo no modo experimental não há variabilidade."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    print(f"📐 Treino: {X_train.shape} | Teste: {X_test.shape}")

    # -------------------------------------------------------------------------
    # 6. TREINAMENTO
    # -------------------------------------------------------------------------
    model = XGBClassifier(
    n_estimators=50,
    max_depth=3,
    min_child_weight=0.1,
    gamma=0,
    learning_rate=0.1,
    subsample=1.0,
    colsample_bytree=1.0,
    eval_metric="logloss",
    random_state=42
    )


    print("🧠 Treinando XGBoost...")
    model.fit(X_train, y_train)

    # -------------------------------------------------------------------------
    # 7. AVALIAÇÃO
    # -------------------------------------------------------------------------
    print("\n📊 Avaliação do modelo (TARGET EXPERIMENTAL):")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, digits=3))

    # -------------------------------------------------------------------------
    # 8. SALVAMENTO
    # -------------------------------------------------------------------------
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    model.save_model(MODEL_OUTPUT_PATH)
    print(f"✅ Modelo salvo em: {MODEL_OUTPUT_PATH}")

    # -------------------------------------------------------------------------
    # 9. IMPORTÂNCIA DAS FEATURES
    # -------------------------------------------------------------------------
    importances = (
        pd.DataFrame(
            {
                "Feature": X.columns,
                "Importance": model.feature_importances_,
            }
        )
        .sort_values(by="Importance", ascending=False)
    )

    print("\n🔍 Top 20 variáveis mais importantes:")
    print(importances.head(20))


# =============================================================================
# ENTRYPOINT
# =============================================================================

if __name__ == "__main__":
    train_model()
