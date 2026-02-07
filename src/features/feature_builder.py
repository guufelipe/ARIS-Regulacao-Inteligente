import pandas as pd
import numpy as np

class FeatureBuilder:
    def __init__(self):
        """
        Classe responsável por preparar dados tabulares finais
        após parsing + NLP.

        Princípios:
        - Não imputar valores clínicos contínuos
        - Não permitir texto cru no modelo
        - Garantir consistência treino / inferência
        """
        pass

    def fit(self, df):
        return self

    def transform(self, df):
        df_clean = df.copy()

        # =====================================================
        # 1. IDADE (Regra de Negócio: Adulto)
        # =====================================================
        if 'Idade' in df_clean.columns:
            df_clean['Idade'] = pd.to_numeric(df_clean['Idade'], errors='coerce')
            df_clean.loc[df_clean['Idade'] < 15, 'Idade'] = np.nan

        # =====================================================
        # 2. SEXO
        # =====================================================
        if 'Sexo' in df_clean.columns:
            df_clean['Sexo_Encoded'] = df_clean['Sexo'].apply(
                lambda x: 1 if str(x).strip().upper().startswith('M') else 0
            )

        # =====================================================
        # 3. FLAGS MÉDICAS BINÁRIAS
        # =====================================================
        flags_importantes = [
            'Necessidade_Dialise', 
            'Sinais_Vitais_O2_Suporte', 
            'Instabilidade_Hemodinamica', 
            'Hemorragia_Ativa',
            'Suspeita_Infecciosa', 
            'Oncologia_Fora_Perfil',
            'Sinais_Gastro_Hepato'
        ]

        for col in flags_importantes:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna(0).astype(int)

        # =====================================================
        # 4. PROTEÇÃO DAS FEATURES TF-IDF
        # =====================================================
        tfidf_cols = [c for c in df_clean.columns if c.startswith('tfidf_')]
        for col in tfidf_cols:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)

        # =====================================================
        # 5. REMOÇÃO DE TEXTO CRU (ANTI-VAZAMENTO)
        # =====================================================
        colunas_texto = [
            'Justificativa_Internacao',
            'Evolucao',
            'Sinais_Vitais_Texto',
            'Diagnostico_Texto_Livre'
        ]

        df_clean.drop(
            columns=[c for c in colunas_texto if c in df_clean.columns],
            inplace=True,
            errors='ignore'
        )

        return df_clean
