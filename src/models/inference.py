"""
Arquivo: models/inference.py

Responsável por:
- Carregar os artefatos treinados (modelo XGBoost + TF-IDF)
- Aplicar regras soberanas de exclusão (camada de segurança clínica)
- Executar inferência de IA apenas quando permitido pelo protocolo
- Retornar decisão explicável (aprovado / reprovado + probabilidade)

Arquitetura:
REGRAS CLÍNICAS (hard rules)  ->  MODELO DE IA (soft decision)
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier

# =========================================================
# AJUSTE DE PATHS (robusto para rodar de qualquer lugar)
# =========================================================

# Caminho absoluto deste arquivo (models/inference.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Sobe dois níveis: models -> src -> raiz do projeto
project_root = os.path.dirname(os.path.dirname(current_dir))

# Garante que a raiz está no PYTHONPATH
if project_root not in sys.path:
    sys.path.append(project_root)

# Caminhos absolutos dos artefatos treinados
MODEL_PATH = os.path.join(project_root, 'models', 'xgboost_model.json')
VECTORIZER_PATH = os.path.join(
    project_root, 'models', 'vectorizers', 'tfidf_vectorizer.pkl'
)

# =========================================================
# CLASSE PRINCIPAL DE INFERÊNCIA
# =========================================================

class ArisPredictor:
    """
    Motor de inferência do sistema ARIS.

    Responsabilidades:
    - Garantir segurança clínica via regras soberanas
    - Preparar dados exatamente como no treino
    - Executar inferência e retornar decisão interpretável
    """

    def __init__(self):
        """
        Inicializa o preditor carregando:
        - Modelo XGBoost treinado
        - Vetorizador TF-IDF
        """
        print("🤖 Inicializando o motor de inferência ARIS...")
        print(f"📂 Raiz do projeto detectada em: {project_root}")

        # Verificação defensiva
        if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
            raise FileNotFoundError(
                f"❌ Artefatos de modelo não encontrados.\n"
                f"Modelo esperado em: {MODEL_PATH}\n"
                f"Vetorizador esperado em: {VECTORIZER_PATH}\n"
                f"➡️ Execute train_xgboost.py antes da inferência."
            )

        # Carrega o modelo
        self.model = XGBClassifier()
        self.model.load_model(MODEL_PATH)

        # Carrega o vetorizador NLP
        self.vectorizer = joblib.load(VECTORIZER_PATH)

        print("✅ Modelo e vetorizador carregados com sucesso.")

    # =====================================================
    # MÉTODO PRINCIPAL DE PREDIÇÃO
    # =====================================================

    def predict_new_case(self, dados_paciente: dict) -> dict:
        """
        Executa a inferência para um novo caso clínico.

        Fluxo:
        1. Camada de Segurança (regras soberanas)
        2. Preparação das features estruturadas
        3. Vetorização do texto clínico
        4. Alinhamento com features do modelo
        5. Predição probabilística

        Retorno:
        dict com decisão final e probabilidade
        """

        # -------------------------------------------------
        # 0. CAMADA DE SEGURANÇA (HARD RULES)
        # -------------------------------------------------
        # Qualquer um desses critérios bloqueia o paciente
        # independentemente do texto ou da IA.
        criterios_exclusao_soberanos = [
            'Necessidade_Dialise',
            'Sinais_Vitais_O2_Suporte',
            'Instabilidade_Hemodinamica',
            'Hemorragia_Ativa',
            'Suspeita_Infecciosa',
            'Oncologia_Fora_Perfil'
        ]

        bloqueios_ativos = []

        for criterio in criterios_exclusao_soberanos:
            if dados_paciente.get(criterio, 0) == 1:
                bloqueios_ativos.append(criterio)

        # Short-circuit: reprovação imediata
        if bloqueios_ativos:
            motivo = ", ".join(bloqueios_ativos)
            print(f"🚫 Bloqueio de segurança ativado por: {motivo}")

            return {
                "aprovado": False,
                "probabilidade_percentual": 0.0,
                "diagnostico_modelo": f"REPROVADO POR PROTOCOLO ({motivo})"
            }

        # -------------------------------------------------
        # 1. CONVERSÃO PARA DATAFRAME
        # -------------------------------------------------
        df_input = pd.DataFrame([dados_paciente])

        # -------------------------------------------------
        # 2. FEATURE ENGINEERING TABULAR
        # -------------------------------------------------

        # A) Codificação simples de sexo (compatível com treino)
        if 'Sexo' in df_input.columns:
            df_input['Sexo_Encoded'] = df_input['Sexo'].apply(
                lambda x: 1 if str(x).strip().upper().startswith('M') else 0
            )
        else:
            df_input['Sexo_Encoded'] = 0

        # B) Garantia de flags binárias esperadas
        # Incluímos também Sinais_Gastro_Hepato (feature positiva)
        cols_flags = criterios_exclusao_soberanos + ['Sinais_Gastro_Hepato']

        for col in cols_flags:
            df_input[col] = df_input.get(col, 0)

        # C) Tratamento da idade (modelo aceita NaN, mas padronizamos)
        df_input['Idade'] = pd.to_numeric(
            df_input.get('Idade', 0),
            errors='coerce'
        ).fillna(0)

        # -------------------------------------------------
        # 3. PROCESSAMENTO NLP
        # -------------------------------------------------
        from src.features.text_vectorization import clean_text_for_nlp

        texto_bruto = dados_paciente.get('Diagnostico_Texto_Livre', '')
        texto_limpo = clean_text_for_nlp(texto_bruto)

        # Vetorização TF-IDF
        tfidf_matrix = self.vectorizer.transform([texto_limpo])
        feature_names = self.vectorizer.get_feature_names_out()

        df_tfidf = pd.DataFrame(
            tfidf_matrix.toarray(),
            columns=[f"tfidf_{w}" for w in feature_names]
        )

        # -------------------------------------------------
        # 4. DATASET FINAL PARA O MODELO
        # -------------------------------------------------
        df_final = pd.concat([df_input, df_tfidf], axis=1)

        # -------------------------------------------------
        # 5. ALINHAMENTO COM AS FEATURES DO TREINO
        # -------------------------------------------------
        # O XGBoost exige exatamente as mesmas colunas
        colunas_esperadas = self.model.get_booster().feature_names

        for col in colunas_esperadas:
            if col not in df_final.columns:
                df_final[col] = 0

        X_input = df_final[colunas_esperadas]

        # -------------------------------------------------
        # 6. PREDIÇÃO
        # -------------------------------------------------
        probabilidade = self.model.predict_proba(X_input)[0][1]

        return {
            "aprovado": probabilidade > 0.5,
            "probabilidade_percentual": round(probabilidade * 100, 2),
            "diagnostico_modelo": (
                "ADERENTE AO PERFIL"
                if probabilidade > 0.5
                else "REJEITADO (PERFIL INADEQUADO)"
            )
        }

# =========================================================
# BLOCO DE TESTE LOCAL
# =========================================================

if __name__ == "__main__":
    """
    Teste rápido:
    - Texto favorável
    - Critério soberano ativo (O2)
    - Deve reprovar SEM consultar a IA
    """
    try:
        predictor = ArisPredictor()

        caso_teste = {
            'Idade': 55,
            'Sexo': 'MASCULINO',
            'Necessidade_Dialise': 0,
            'Sinais_Vitais_O2_Suporte': 1,  # critério bloqueante
            'Instabilidade_Hemodinamica': 0,
            'Hemorragia_Ativa': 0,
            'Suspeita_Infecciosa': 0,
            'Oncologia_Fora_Perfil': 0,
            'Sinais_Gastro_Hepato': 1,
            'Diagnostico_Texto_Livre': 'paciente com ascite volumosa, baixo risco.'
        }

        print("\n--- 🧪 TESTE DE SEGURANÇA ---")
        resultado = predictor.predict_new_case(caso_teste)
        print(resultado)

    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
