import os
import pandas as pd
from src.extraction.pdf_extractor import extract_text_from_pdf
from src.parsing.parser_espelho import parse_text_to_dict

# Configurações de diretórios
RAW_DIR = 'data/raw'
PROCESSED_DIR = 'data/processed'

def main():
    # Garante que a pasta de saída existe
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    arquivos = [f for f in os.listdir(RAW_DIR) if f.endswith('.pdf')]
    print(f"🚀 Iniciando pipeline ARIS. Encontrados {len(arquivos)} arquivos.")

    dataset = []

    for arquivo in arquivos:
        print(f"Processando: {arquivo}...")
        caminho_completo = os.path.join(RAW_DIR, arquivo)
        
        # 1. Extração
        texto = extract_text_from_pdf(caminho_completo)
        
        if texto:
            # 2. Parsing
            features = parse_text_to_dict(texto)
            features['Nome_Arquivo'] = arquivo # Rastreabilidade
            dataset.append(features)
        else:
            print(f"⚠️ Aviso: Nenhum texto extraído de {arquivo}. Pode ser uma imagem escaneada?")

    # 3. Salvamento
    if dataset:
        df = pd.DataFrame(dataset)
        
        # Reordenando colunas para facilitar leitura
        cols = ['Nome_Arquivo', 'Idade', 'Diagnostico_Texto_Livre'] + [c for c in df.columns if c not in ['Nome_Arquivo', 'Idade', 'Diagnostico_Texto_Livre']]
        df = df[cols]
        
        output_file = os.path.join(PROCESSED_DIR, 'dataset_espelhos.csv')
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ Sucesso! {len(df)} registros processados.")
        print(f"💾 Arquivo salvo em: {output_file}")
        print("\n--- Amostra dos Dados ---")
        print(df.head())
    else:
        print("\n❌ Nenhum dado foi processado.")

if __name__ == "__main__":
    main()