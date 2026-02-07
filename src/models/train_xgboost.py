"""
Treinamento do modelo XGBoost do projeto ARIS.

Este script:
- Utiliza dados clínicos extraídos de espelhos de regulação
- Combina regras clínicas (flags tabulares) com NLP (TF-IDF)
- Treina um modelo supervisionado com target heurístico (provisório)

IMPORTANTE:
O target ainda NÃO representa a decisão real da regulação.
Ele simula a lógica do protocolo oficial enquanto não há rótulos reais.
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


# =============================================================================
# CONFIGURAÇÕES DE CAMINHO
# =============================================================================

PROCESSED_DATA_PATH = 'data/processed/dataset_espelhos.csv'
MODEL_OUTPUT_PATH = 'models/xgboost_model.json'
VECTORIZER_PATH = 'models/vectorizers/tfidf_vectorizer.pkl'


# =============================================================================
# TARGET HEURÍSTICO (PROVISÓRIO)
# =============================================================================

def gerar_target_simulado(row):
    """
    Gera um rótulo binário (Target) simulando a decisão da regulação,
    baseado estritamente nas regras do protocolo.

    Retorna:
    1 → Caso elegível para gastro
    0 → Caso NÃO elegível
    """

    # Critérios de exclusão são soberanos
    if (
        row['Necessidade_Dialise'] == 1 or
        row['Sinais_Vitais_O2_Suporte'] == 1 or
        row['Instabilidade_Hemodinamica'] == 1 or
        row['Hemorragia_Ativa'] == 1 or
        row['Suspeita_Infecciosa'] == 1 or
        row['Oncologia_Fora_Perfil'] == 1
    ):
        return 0

    # Critério de inclusão (perfil gastro)
    if row['Sinais_Gastro_Hepato'] == 1:
        return 1

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
    # 2. GERAÇÃO DO TARGET (HEURÍSTICO)
    # -------------------------------------------------------------------------
    print("🎯 Gerando target heurístico baseado no protocolo...")
    df['Target'] = df.apply(gerar_target_simulado, axis=1)

    print("⚖️ Distribuição das classes:")
    print(df['Target'].value_counts())

    # -------------------------------------------------------------------------
    # 3. VETORIZAÇÃO DOS TEXTOS CLÍNICOS (NLP)
    # -------------------------------------------------------------------------
    print("🔠 Vetorizando textos clínicos com TF-IDF...")

    # Campos textuais relevantes do espelho
    TEXT_COLUMNS = [
        'Justificativa_Internacao',
        'Evolucao',
        'Sinais_Vitais_Texto'
    ]

    df_nlp, vectorizer = vectorize_text(
        df,
        text_columns=TEXT_COLUMNS,
        max_features=300  # Espaço maior para capturar termos clínicos
    )

    if vectorizer is None:
        print("❌ Falha na vetorização (textos vazios). Abortando treino.")
        return

    # Salva o vetorizador para uso em inferência
    os.makedirs(os.path.dirname(VECTORIZER_PATH), exist_ok=True)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"💾 Vetorizador salvo em: {VECTORIZER_PATH}")

    # -------------------------------------------------------------------------
    # 4. FEATURE BUILDER (TABULAR FINAL)
    # -------------------------------------------------------------------------
    print("🔧 Aplicando FeatureBuilder (limpeza e validação final)...")

    builder = FeatureBuilder()
    df_final = builder.transform(df_nlp)

    # Aviso de integridade da idade
    if 'Idade' in df_final.columns:
        nulos_idade = df_final['Idade'].isna().sum()
        if nulos_idade > 0:
            print(f"⚠️ {nulos_idade} registros com Idade inválida (NaN).")

    # -------------------------------------------------------------------------
    # 5. SEPARAÇÃO DE FEATURES E TARGET
    # -------------------------------------------------------------------------
    print("🧱 Preparando matriz de treino...")

    X = df_final.drop(columns=['Target'])
    y = df_final['Target']

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y
    )

    print(f"📐 Treino: {X_train.shape} | Teste: {X_test.shape}")

    # -------------------------------------------------------------------------
    # 6. TREINAMENTO DO MODELO
    # -------------------------------------------------------------------------
    model = XGBClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=3,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='logloss',
        missing=np.nan,
        random_state=42
    )

    print("🧠 Treinando XGBoost...")
    model.fit(X_train, y_train)

    # -------------------------------------------------------------------------
    # 7. AVALIAÇÃO
    # -------------------------------------------------------------------------
    print("\n📊 Avaliação do modelo (Target heurístico):")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, digits=3))

    # -------------------------------------------------------------------------
    # 8. SALVAMENTO DO MODELO
    # -------------------------------------------------------------------------
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    model.save_model(MODEL_OUTPUT_PATH)
    print(f"✅ Modelo salvo em: {MODEL_OUTPUT_PATH}")

    # -------------------------------------------------------------------------
    # 9. IMPORTÂNCIA DAS FEATURES
    # -------------------------------------------------------------------------
    importances = (
        pd.DataFrame({
            'Feature': X.columns,
            'Importance': model.feature_importances_
        })
        .sort_values(by='Importance', ascending=False)
    )

    print("\n🔍 Top 10 variáveis mais importantes:")
    print(importances.head(10))


# =============================================================================
# ENTRYPOINT
# =============================================================================

if __name__ == "__main__":
    train_model()
