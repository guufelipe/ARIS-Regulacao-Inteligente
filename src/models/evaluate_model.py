import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBClassifier
from sklearn.metrics import confusion_matrix, roc_curve, auc
from src.models.train_xgboost import PROCESSED_DATA_PATH, MODEL_OUTPUT_PATH, gerar_target_simulado
from src.features.text_vectorization import vectorize_text

def evaluate():
    print("📊 Iniciando avaliação detalhada do meu modelo...")

    # 1. Carregar Dados e Modelo
    # Preciso refazer o processamento para garantir que as features batam
    df = pd.read_csv(PROCESSED_DATA_PATH)
    df['Target'] = df.apply(gerar_target_simulado, axis=1) # Recrio o target para ter com o que comparar
    
    # Trato nulos igual no treino
    df['Idade'] = df['Idade'].fillna(df['Idade'].mean())

    # Vetorização (importante: em produção eu carregaria o pickle, aqui recrio para simplificar a validação)
    df_full, _ = vectorize_text(df, text_column='Diagnostico_Texto_Livre', max_features=50)
    
    cols_to_drop = ['Nome_Arquivo', 'Diagnostico_Texto_Livre', 'Sexo', 'CID_10', 'Target']
    X = df_full[[c for c in df_full.columns if c not in cols_to_drop]]
    y_true = df_full['Target']

    # Carrego o modelo que treinei
    model = XGBClassifier()
    model.load_model(MODEL_OUTPUT_PATH)
    
    # 2. Previsões
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]

    # 3. Matriz de Confusão
    # Quero ver onde estou errando: Falso Positivo ou Falso Negativo?
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
    plt.title('Minha Matriz de Confusão')
    plt.xlabel('O que o modelo previu')
    plt.ylabel('Realidade (Simulada)')
    plt.show()

    # 4. Curva ROC
    # Avalio a capacidade de discriminação do modelo
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'Curva ROC (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Taxa de Falsos Positivos')
    plt.ylabel('Taxa de Verdadeiros Positivos')
    plt.title('Performance do Classificador ARIS')
    plt.legend(loc="lower right")
    plt.show()

if __name__ == "__main__":
    evaluate()