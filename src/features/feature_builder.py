import pandas as pd
import numpy as np

class FeatureBuilder:
    def __init__(self):
        """
        Classe responsável por limpar e preparar os dados tabulares.
        
        CORREÇÃO DE LÓGICA: 
        Não realizamos imputação de média em Idade. Se a idade estiver faltando
        ou for inválida (< 18), tratamos como NaN. A integridade do dado é prioritária.
        """
        pass

    def fit(self, df):
        """
        Neste pipeline estrito, não precisamos 'aprender' médias, 
        pois não faremos imputação estatística.
        Mantido para compatibilidade com a interface do scikit-learn.
        """
        return self

    def transform(self, df):
        """
        Aplica as transformações nos dados:
        1. Validação de Idade (Idade < 18 vira NaN)
        2. Encoding de Sexo
        3. Garantia de Flags Numéricas
        """
        # Crio uma cópia para não alterar o dataframe original por acidente
        df_clean = df.copy()

        # --- 1. Tratamento Rigoroso de Idade ---
        if 'Idade' in df_clean.columns:
            # Garante que é numérico
            df_clean['Idade'] = pd.to_numeric(df_clean['Idade'], errors='coerce')
            
            # REGRA DE NEGÓCIO: Enfermaria Adulto.
            # Se a idade for < 18, assumimos erro de parsing ou dado inválido.
            # Transformamos em NaN para o XGBoost tratar como "Valor Desconhecido".
            df_clean.loc[df_clean['Idade'] < 18, 'Idade'] = np.nan

        # --- 2. Encoding de Sexo ---
        # 1 = Masculino, 0 = Feminino/Outros
        if 'Sexo' in df_clean.columns:
            df_clean['Sexo_Encoded'] = df_clean['Sexo'].apply(
                lambda x: 1 if str(x).strip().upper().startswith('M') else 0
            )

        # --- 3. Garantia de Flags Numéricas ---
        # Garanto que todas as colunas de Sim/Não sejam inteiros (0 ou 1)
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
                # Aqui mantemos fillna(0) apenas para flags booleanas, 
                # assumindo que se não foi detectado, é negativo.
                df_clean[col] = df_clean[col].fillna(0).astype(int)

        return df_clean