"""
Pipeline de ingestão do ARIS: varro PDFs em data/raw, extraio o texto,
faço o parsing para features estruturadas e salvo o dataset consolidado
em data/processed/dataset_espelhos.csv.

Como rodar (Windows/PowerShell):
1) (Opcional) Criar e ativar um ambiente virtual
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
2) Instalar dependências
     pip install -r requirements.txt
3) Executar o pipeline de ingestão
     python run_ingestion.py

Como rodar de novo (reprocessar):
- Basta executar novamente o comando acima; o arquivo dataset_espelhos.csv
    será sobrescrito com o resultado mais recente.

Quando eu adiciono novos dados em data/raw:
- Coloco os novos PDFs na pasta data/raw e executo o script de novo.
- Arquivos já processados podem ser processados novamente sem problemas; o CSV final
    sempre reflete o que houver na pasta no momento da execução.

Dicas e observações:
- Se algum PDF não tiver texto extraível (por ser imagem escaneada), o log irá avisar.
    Nesses casos, considerar um passo de OCR (ver utilitários em src/extraction/ocr_utils.py, se aplicável)
    antes de reprocessar.
- A estrutura final de colunas depende de parse_text_to_dict; ao menos inclui Nome_Arquivo,
    Idade e Diagnostico_Texto_Livre, além das flags clínicas derivadas.
"""

import os
import pandas as pd
from src.extraction.pdf_extractor import extract_text_from_pdf
from src.parsing.parser_espelho import parse_text_to_dict

# Configurações de diretórios
# RAW_DIR: onde coloco os PDFs de entrada (arquivos brutos)
# PROCESSED_DIR: onde salvo o CSV consolidado gerado pelo pipeline
RAW_DIR = 'data/raw'
PROCESSED_DIR = 'data/processed'

def main():
    # 0) Preparação: garanto que a pasta de saída existe
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # 1) Varredura: listo todos os PDFs disponíveis em data/raw
    #    Dica: para reprocessar com novos dados, basta adicionar PDFs aqui e rodar novamente.
    arquivos = [f for f in os.listdir(RAW_DIR) if f.endswith('.pdf')]
    print(f"🚀 Iniciando pipeline ARIS. Encontrados {len(arquivos)} arquivos.")

    dataset = []

    for arquivo in arquivos:
        print(f"Processando: {arquivo}...")
        caminho_completo = os.path.join(RAW_DIR, arquivo)
        
        # 2) Extração: extraio o texto bruto do PDF
        texto = extract_text_from_pdf(caminho_completo)
        
        if texto:
            # 3) Parsing: transformo o texto em um dicionário de features estruturadas
            features = parse_text_to_dict(texto)
            features['Nome_Arquivo'] = arquivo # Rastreabilidade do registro
            dataset.append(features)
        else:
            # Caso comum em PDFs escaneados sem OCR; considerar etapa de OCR antes de reprocessar
            print(f"⚠️ Aviso: Nenhum texto extraído de {arquivo}. Pode ser uma imagem escaneada?")

    # 4) Salvamento: consolido tudo em um único CSV para consumo pelos próximos estágios
    if dataset:
        df = pd.DataFrame(dataset)
        
        # Reordeno colunas para facilitar a leitura e inspeção inicial do dataset
        cols = ['Nome_Arquivo', 'Idade', 'Diagnostico_Texto_Livre'] + [c for c in df.columns if c not in ['Nome_Arquivo', 'Idade', 'Diagnostico_Texto_Livre']]
        df = df[cols]
        
        output_file = os.path.join(PROCESSED_DIR, 'dataset_espelhos.csv')
        df.to_csv(output_file, index=False)
        
        # Observação: re-execuções sobrescrevem este arquivo com os dados atuais de data/raw
        print(f"\n✅ Sucesso! {len(df)} registros processados.")
        print(f"💾 Arquivo salvo em: {output_file}")
        print("\n--- Amostra dos Dados ---")
        print(df.head())
    else:
        print("\n❌ Nenhum dado foi processado.")

if __name__ == "__main__":
    main()