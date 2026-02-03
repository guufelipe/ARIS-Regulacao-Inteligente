import pandas as pd
import joblib
import os
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from src.features.text_vectorization import vectorize_text
from src.features.feature_builder import FeatureBuilder # <--- Importando a nova classe

# Meus caminhos de arquivo
PROCESSED_DATA_PATH = 'data/processed/dataset_espelhos.csv'
MODEL_OUTPUT_PATH = 'models/xgboost_model.json'
VECTORIZER_PATH = 'models/vectorizers/tfidf_vectorizer.pkl'

def gerar_target_simulado(row):
    """
    Gera targets simulados baseados nas regras de negócio (Heurística).
    Necessário pois ainda não temos o feedback real da regulação (Aprovado/Reprovado).
    """
    # Critérios de exclusão soberanos
    if (row['Necessidade_Dialise'] == 1 or 
        row['Sinais_Vitais_O2_Suporte'] == 1 or 
        row['Instabilidade_Hemodinamica'] == 1 or
        row['Hemorragia_Ativa'] == 1 or
        row['Suspeita_Infecciosa'] == 1 or
        row['Oncologia_Fora_Perfil'] == 1):
        return 0
    
    # Critério de inclusão
    if row['Sinais_Gastro_Hepato'] == 1:
        return 1
        
    return 0

def train_model():
    print("🚀 Iniciei o treinamento do modelo ARIS (Modo Estrito - Sem Imputação)...")
    
    # 1. Carregamento
    if not os.path.exists(PROCESSED_DATA_PATH):
        print(f"❌ Não encontrei o arquivo em {PROCESSED_DATA_PATH}. Rode run_ingestion.py primeiro.")
        return

    df = pd.read_csv(PROCESSED_DATA_PATH)
    print(f"📊 Carreguei {df.shape[0]} registros para análise.")

    # 2. Engenharia de Features Tabulares (FeatureBuilder)
    print("🔧 Aplicando limpeza de dados (FeatureBuilder)...")
    builder = FeatureBuilder()
    builder.fit(df) # Não faz nada no modo atual, mas mantemos o padrão
    df = builder.transform(df)

    # Verificação de integridade
    nulos_idade = df['Idade'].isna().sum()
    if nulos_idade > 0:
        print(f"⚠️ Aviso: Existem {nulos_idade} registros com Idade inválida/nula. O XGBoost lidará com eles.")

    # 3. Geração do Target (Provisório)
    print("🎯 Gerando targets simulados...")
    df['Target'] = df.apply(gerar_target_simulado, axis=1)
    
    print("⚖️ Distribuição das Classes (0=Reprova, 1=Aprova):")
    print(df['Target'].value_counts())

    # 4. Vetorização (NLP)
    print("🔠 Vetorizando o texto clínico...")
    df_full, vectorizer = vectorize_text(df, text_column='Diagnostico_Texto_Livre', max_features=50)
    
    # Se a vetorização falhar (texto vazio), interrompe
    if vectorizer is None:
        print("❌ Erro fatal na vetorização. Abortando.")
        return

    # Salvo o vetorizador
    os.makedirs(os.path.dirname(VECTORIZER_PATH), exist_ok=True)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"💾 Vetorizador salvo em: {VECTORIZER_PATH}")

    # 5. Preparação para o Treino
    # Removo colunas que não entram no modelo
    cols_to_drop = ['Nome_Arquivo', 'Sexo', 'CID_10', 'Target']
    features = [c for c in df_full.columns if c not in cols_to_drop]
    
    X = df_full[features]
    y = df_full['Target']

    # Separo Treino e Teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # 6. Treinamento do XGBoost
    model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        use_label_encoder=False,
        eval_metric='logloss',
        missing=np.nan  # Explicitamente dizemos ao modelo como tratar nulos
    )
    
    print("🧠 Treinando o modelo...")
    model.fit(X_train, y_train)

    # 7. Avaliação
    print("\n--- Resultados do Modelo ---")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    model.save_model(MODEL_OUTPUT_PATH)
    print(f"\n✅ Modelo salvo em: {MODEL_OUTPUT_PATH}")

    # 8. Importância das Variáveis
    importances = pd.DataFrame({
        'Feature': features,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    print("\n🔍 Variáveis mais importantes:")
    print(importances.head(5))

if __name__ == "__main__":
    train_model()