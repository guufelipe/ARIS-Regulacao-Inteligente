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
# AJUSTE DE PATHS
# =========================================================

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

if project_root not in sys.path:
    sys.path.append(project_root)

MODEL_PATH = os.path.join(project_root, 'models', 'xgboost_model.json')
VECTORIZER_PATH = os.path.join(
    project_root, 'models', 'vectorizers', 'tfidf_vectorizer.pkl'
)

# =========================================================
# CLASSE PRINCIPAL
# =========================================================

class ArisPredictor:
    """
    Motor de inferência do sistema ARIS.
    """

    def __init__(self):
        print("🤖 Inicializando o motor de inferência ARIS...")
        print(f"📂 Raiz do projeto: {project_root}")

        if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
            raise FileNotFoundError(
                "❌ Artefatos do modelo não encontrados.\n"
                "➡️ Execute o pipeline de treino antes da inferência."
            )

        self.model = XGBClassifier()
        self.model.load_model(MODEL_PATH)

        self.vectorizer = joblib.load(VECTORIZER_PATH)

        print("✅ Modelo e vetorizador carregados com sucesso.")

    # =====================================================
    # PREDIÇÃO
    # =====================================================

    def predict_new_case(self, dados_paciente: dict) -> dict:

        # -------------------------------------------------
        # 0. REGRAS SOBERANAS
        # -------------------------------------------------
        criterios_exclusao_soberanos = [
            'Necessidade_Dialise',
            'Sinais_Vitais_O2_Suporte',
            'Instabilidade_Hemodinamica',
            'Hemorragia_Ativa',
            'Suspeita_Infecciosa',
            'Oncologia_Fora_Perfil'
        ]

        bloqueios = [
            c for c in criterios_exclusao_soberanos
            if dados_paciente.get(c, 0) == 1
        ]

        if bloqueios:
            motivo = ", ".join(bloqueios)
            return {
                "aprovado": False,
                "probabilidade_percentual": 0.0,
                "diagnostico_modelo": f"REPROVADO POR PROTOCOLO ({motivo})"
            }

        # -------------------------------------------------
        # 1. BASE TABULAR
        # -------------------------------------------------
        df_input = pd.DataFrame([dados_paciente])

        # Sexo
        df_input['Sexo_Encoded'] = df_input.get('Sexo', '').apply(
            lambda x: 1 if str(x).upper().startswith('M') else 0
        )

        # Flags binárias
        for col in criterios_exclusao_soberanos + ['Sinais_Gastro_Hepato']:
            df_input[col] = df_input.get(col, 0)

        # Idade
        df_input['Idade'] = pd.to_numeric(
            df_input.get('Idade', 0),
            errors='coerce'
        ).fillna(0)

        # -------------------------------------------------
        # 2. NLP — MESMA LÓGICA DO TREINO
        # -------------------------------------------------
        from src.features.text_vectorization import (
            basic_text_clean,
            extract_clinical_numeric_tokens
        )

        texto_bruto = dados_paciente.get('Diagnostico_Texto_Livre', '')

        texto_limpo = basic_text_clean(texto_bruto)
        tokens_numericos = extract_clinical_numeric_tokens(texto_limpo)

        # IMPORTANTE: prefixo igual ao treino
        texto_final = (
            f"diagnostico_texto_livre "
            f"{texto_limpo} "
            f"{' '.join(tokens_numericos)}"
        )

        tfidf_matrix = self.vectorizer.transform([texto_final])
        feature_names = self.vectorizer.get_feature_names_out()

        df_tfidf = pd.DataFrame(
            tfidf_matrix.toarray(),
            columns=[f"tfidf_{f}" for f in feature_names]
        )

        # -------------------------------------------------
        # 3. DATASET FINAL
        # -------------------------------------------------
        df_final = pd.concat([df_input, df_tfidf], axis=1)

        colunas_esperadas = self.model.get_booster().feature_names

        for col in colunas_esperadas:
            if col not in df_final.columns:
                df_final[col] = 0

        X = df_final[colunas_esperadas]

        # -------------------------------------------------
        # 4. PREDIÇÃO
        # -------------------------------------------------
        prob = self.model.predict_proba(X)[0][1]

        return {
            "aprovado": prob >= 0.5,
            "probabilidade_percentual": round(prob * 100, 2),
            "diagnostico_modelo": (
                "ADERENTE AO PERFIL"
                if prob >= 0.5
                else "REJEITADO (PERFIL INADEQUADO)"
            )
        }


# =========================================================
# TESTE LOCAL
# =========================================================

if __name__ == "__main__":
    predictor = ArisPredictor()

    caso = {
        'Idade': 60,
        'Sexo': 'MASCULINO',
        'Necessidade_Dialise': 0,
        'Sinais_Vitais_O2_Suporte': 0,
        'Instabilidade_Hemodinamica': 0,
        'Hemorragia_Ativa': 0,
        'Suspeita_Infecciosa': 0,
        'Oncologia_Fora_Perfil': 0,
        'Sinais_Gastro_Hepato': 1,
        'Diagnostico_Texto_Livre': 'Paciente com ascite volumosa, satO2 96, PA 120x80.'
    }

    print(predictor.predict_new_case(caso))
