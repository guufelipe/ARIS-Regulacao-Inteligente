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


"""
ARIS – Pipeline de Ingestão e Parsing de Espelhos Clínicos

Responsabilidade:
- Ler PDFs brutos em data/raw
- Extrair texto
- Aplicar parsing semântico (parser_espelho)
- Gerar dataset tabular estruturado (CSV)

Este script NÃO:
- Treina modelos
- Faz NLP vetorial
- Aplica IA

Pipeline:
PDF → Texto → Parsing clínico → CSV consolidado
"""

"""
ARIS – Pipeline de Ingestão e Parsing de Espelhos Clínicos
"""

import os
import pandas as pd
from src.extraction.pdf_extractor import extract_text_from_pdf
from src.parsing.parser_espelho import parse_text_to_dict

# ===============================
# Configurações de Diretório
# ===============================

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_FILE = "dataset_espelhos.csv"

# ===============================
# Contrato mínimo de colunas
# ===============================

EXPECTED_COLUMNS = [
    "Nome_Arquivo",
    "Idade",
    "Sexo",
    "Justificativa_Internacao",
    "Evolucao",
    "Sinais_Vitais",
    "Necessidade_Dialise",
    "Sinais_Vitais_O2_Suporte",
    "Instabilidade_Hemodinamica",
    "Hemorragia_Ativa",
    "Suspeita_Infecciosa",
    "Oncologia_Fora_Perfil",
    "Sinais_Gastro_Hepato",
    "CID_10",
]

# ===============================
# Função principal
# ===============================

def main():
    print("🚀 Iniciando pipeline de ingestão ARIS")

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    arquivos_pdf = [
        f for f in os.listdir(RAW_DIR)
        if f.lower().endswith(".pdf")
    ]

    print(f"📂 PDFs encontrados em {RAW_DIR}: {len(arquivos_pdf)}")

    if not arquivos_pdf:
        print("⚠️ Nenhum PDF encontrado. Encerrando.")
        return

    registros = []  # ✅ lista correta

    # ===============================
    # Loop principal
    # ===============================
    for nome_arquivo in arquivos_pdf:
        print(f"➡️ Processando: {nome_arquivo}")
        caminho_pdf = os.path.join(RAW_DIR, nome_arquivo)

        texto_bruto = extract_text_from_pdf(caminho_pdf)

        if not texto_bruto or len(texto_bruto.strip()) < 20:
            print(f"⚠️ Texto insuficiente em {nome_arquivo}. Possível PDF escaneado.")
            continue

        try:
            dados = parse_text_to_dict(texto_bruto)
            dados["Nome_Arquivo"] = nome_arquivo
            registros.append(dados)  # ✅ ESSENCIAL

        except Exception as e:
            print(f"❌ Erro ao parsear {nome_arquivo}: {e}")

    # ===============================
    # Consolidação final
    # ===============================
    if not registros:
        print("❌ Nenhum registro válido foi processado.")
        return

    df = pd.DataFrame(registros)

    # Garantia de schema
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[EXPECTED_COLUMNS]

    output_path = os.path.join(PROCESSED_DIR, OUTPUT_FILE)
    df.to_csv(output_path, index=False)

    print("\n✅ Pipeline concluído com sucesso")
    print(f"📊 Registros processados: {len(df)}")
    print(f"💾 Arquivo salvo em: {output_path}")
    print("\n🧪 Amostra dos dados:")
    print(df.head().T)


if __name__ == "__main__":
    main()
