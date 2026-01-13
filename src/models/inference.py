import pandas as pd
import joblib
import numpy as np
from xgboost import XGBClassifier
import os
import sys

# --- CORREÇÃO DE CAMINHOS (PATH) ---
# 1. Pega o caminho absoluto de onde ESTE arquivo (inference.py) está
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Sobe dois níveis para achar a raiz do projeto (src/models -> src -> RAIZ)
project_root = os.path.dirname(os.path.dirname(current_dir))

# 3. Adiciona a raiz ao Python path se não estiver lá
if project_root not in sys.path:
    sys.path.append(project_root)

# 4. Define os caminhos absolutos para os arquivos de modelo
MODEL_PATH = os.path.join(project_root, 'models', 'xgboost_model.json')
VECTORIZER_PATH = os.path.join(project_root, 'models', 'vectorizers', 'tfidf_vectorizer.pkl')

class ArisPredictor:
    def __init__(self):
        """
        Inicializa o motor de inferência carregando os arquivos gerados no treino.
        """
        print("🤖 Inicializando o motor de inferência ARIS...")
        
        # Debug: Mostra onde ele está procurando
        print(f"📂 Buscando artefatos em: {project_root}")
        
        if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
            raise FileNotFoundError(
                f"❌ Arquivos não encontrados!\n"
                f"Esperado Modelo em: {MODEL_PATH}\n"
                f"Esperado Vetor em: {VECTORIZER_PATH}\n"
                "Dica: Rode o 'train_xgboost.py' na raiz do projeto primeiro."
            )

        # Carregar Modelo
        self.model = XGBClassifier()
        self.model.load_model(MODEL_PATH)
        
        # Carregar Vetorizador NLP
        self.vectorizer = joblib.load(VECTORIZER_PATH)
        print("✅ Modelo carregado com sucesso.")

    def predict_new_case(self, dados_paciente):
        """
        ARQUITETURA HÍBRIDA:
        1. Validação de Regras Rígidas (Protocolo de Exclusão)
        2. Inferência de IA (apenas se passar nas regras)
        """
        
        # --- 0. SAFETY LAYER (CAMADA DE SEGURANÇA - NOVO!) ---
        # Regras soberanas que vetam o paciente independente do texto ou da IA.
        # Se qualquer um desses for 1 (True), o paciente é reprovado na hora.
        criterios_exclusao_soberanos = [
            'Necessidade_Dialise', 
            'Sinais_Vitais_O2_Suporte', 
            'Instabilidade_Hemodinamica', 
            'Hemorragia_Ativa', 
            'Suspeita_Infecciosa', 
            'Oncologia_Fora_Perfil'
        ]
        
        reprovas_encontradas = []
        for criterio in criterios_exclusao_soberanos:
            # Verifica se o critério veio no dicionário e se é igual a 1
            if dados_paciente.get(criterio, 0) == 1:
                reprovas_encontradas.append(criterio)
        
        # Se encontrou qualquer bloqueio, REPROVA IMEDIATAMENTE (Short-circuit)
        if reprovas_encontradas:
            motivo = ", ".join(reprovas_encontradas)
            print(f"🚫 Bloqueio de Segurança ativado por: {motivo}")
            return {
                "aprovado": False,
                "probabilidade_percentual": 0.0,
                "diagnostico_modelo": f"REPROVADO POR PROTOCOLO ({motivo})"
            }

        # --- SE PASSOU NA SEGURANÇA, SEGUE PARA A IA ---

        # 1. Converter dicionário para DataFrame
        df_input = pd.DataFrame([dados_paciente])
        
        # 2. Engenharia de Features Tabulares
        # A) Encoding de Sexo
        if 'Sexo' in df_input.columns:
            df_input['Sexo_Encoded'] = df_input['Sexo'].apply(
                lambda x: 1 if str(x).strip().upper().startswith('M') else 0
            )
        else:
            df_input['Sexo_Encoded'] = 0 
        
        # B) Garantia de Flags
        # Adicionamos Sinais_Gastro_Hepato que não é exclusão, mas feature de modelo
        cols_flags = criterios_exclusao_soberanos + ['Sinais_Gastro_Hepato']
        
        for col in cols_flags:
            df_input[col] = df_input.get(col, 0)
            
        # C) Tratamento de Idade
        df_input['Idade'] = pd.to_numeric(df_input['Idade'], errors='coerce').fillna(0)

        # 3. NLP (Vetorização do Texto)
        from src.features.text_vectorization import clean_text_for_nlp
        
        texto_bruto = dados_paciente.get('Diagnostico_Texto_Livre', '')
        texto_limpo = clean_text_for_nlp(texto_bruto)
        
        # Transformar texto em números
        tfidf_matrix = self.vectorizer.transform([texto_limpo])
        feature_names = self.vectorizer.get_feature_names_out()
        df_tfidf = pd.DataFrame(tfidf_matrix.toarray(), columns=[f"tfidf_{w}" for w in feature_names])
        
        # 4. Montagem Final do DataFrame
        df_final = pd.concat([df_input, df_tfidf], axis=1)
        
        # 5. REORDENAMENTO AUTOMÁTICO DE COLUNAS
        colunas_esperadas = self.model.get_booster().feature_names
        
        try:
            for col in colunas_esperadas:
                if col not in df_final.columns:
                    df_final[col] = 0
            
            X_input = df_final[colunas_esperadas]
            
        except Exception as e:
            print(f"❌ Erro ao alinhar colunas: {e}")
            return None

        # 6. Predição da IA
        probabilidade = self.model.predict_proba(X_input)[0][1]
        
        return {
            "aprovado": probabilidade > 0.5,
            "probabilidade_percentual": round(probabilidade * 100, 2),
            "diagnostico_modelo": "ADERENTE AO PERFIL" if probabilidade > 0.5 else "REJEITADO (PERFIL INADEQUADO)"
        }

if __name__ == "__main__":
    # Bloco de Teste Rápido
    try:
        predictor = ArisPredictor()
        
        # --- TESTE DO PROTOCOLO DE SEGURANÇA ---
        # Cenário: Texto ótimo (com a palavra 'baixo'), mas com O2 (critério de exclusão)
        caso_seguranca = {
            'Idade': 55,
            'Sexo': 'MASCULINO',
            'Necessidade_Dialise': 0,
            'Sinais_Vitais_O2_Suporte': 1, # <--- ISSO DEVE BLOQUEAR TUDO
            'Instabilidade_Hemodinamica': 0,
            'Hemorragia_Ativa': 0,
            'Suspeita_Infecciosa': 0,
            'Sinais_Gastro_Hepato': 1,
            'Diagnostico_Texto_Livre': 'paciente com ascite volumosa baixo risco.' # Texto que a IA adora
        }
        
        print("\n--- 🧪 TESTE DE SEGURANÇA (Regras vs IA) ---")
        print(f"Entrada: Texto bom ('baixo risco'), mas usa O2.")
        res = predictor.predict_new_case(caso_seguranca)
        print(f"Resultado Final: {res['diagnostico_modelo']}")
        print(f"Probabilidade: {res['probabilidade_percentual']}%")

    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")