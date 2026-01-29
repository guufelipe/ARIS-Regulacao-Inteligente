# 🏥 ARIS – Apoio Regulatório Inteligente em Saúde  
### Sistema de IA para suporte ao processo de regulação interhospitalar no SUS

---

## 📌 Visão Geral

O **ARIS** é um sistema de Inteligência Artificial desenvolvido no âmbito do Programa de Iniciação Tecnológica (PIT/Ebserh/CNPq), com o objetivo de **analisar automaticamente espelhos de solicitação de regulação** e prever sua **aderência aos perfis regulatórios** dos serviços hospitalares de destino (fase piloto: Gastroenterologia do HC-UFPE).

A solução utiliza:

- Engenharia de Dados  
- NLP (Processamento de Linguagem Natural)  
- Modelagem Preditiva (XGBoost, Random Forest, MLP)  
- Técnicas de explicabilidade (SHAP/LIME)  
- Protótipo de interface de simulação  

O sistema é destinado a apoiar — nunca substituir — a decisão dos reguladores.

---

## 🧱 Arquitetura Geral (3 Fases)

### **Fase 1 — Engenharia de Dados**
- Coleta retrospectiva dos espelhos de solicitação  
- Extração de texto de PDFs (pdfplumber / OCR)  
- Parsing e padronização dos campos clínicos  
- Anonimização (LGPD)  
- Construção do dicionário de variáveis  
- Análise descritiva (frequências, tendências, correlações)  

### **Fase 2 — Modelagem Preditiva**
- NLP para texto clínico (TF-IDF ou embeddings)  
- Divisão treino/validação/teste (70/15/15)  
- Modelos utilizados:
  - XGBoost (principal)
  - Random Forest (baseline)
  - MLP simples
- Avaliação:
  - Acurácia
  - AUC-ROC
  - F1-score
  - Precision–Recall
- Explicabilidade:
  - SHAP
  - LIME  

### **Fase 3 — Protótipo e Simulações**
- Interface web de simulação  
- Retorno da probabilidade de aderência  
- Destacar variáveis mais influentes  
- Simulações retrospectivas com casos reais  
- Medição de impacto:
  - Redução do tempo de triagem
  - Reencaminhamentos evitáveis
  - Concordância com decisões históricas  

---

## 📂 Estrutura do Repositório

ARIS/
│
├── README.md
├── .gitignore
├── requirements.txt
│
├── data/
│   ├── raw/                    # PDFs originais (espelhos) + protocolos
│   └── processed/              # DataFrames finais prontos para modelagem (CSV/Parquet)
│
├── src/
│   ├── extraction/             # Módulos de extração de texto dos PDFs
│   │   ├── pdf_extractor.py
│   │   ├── text_cleaner.py     # Decodificador
│   │   └── ocr_utils.py        # Caso o pdf não seja 'copiavel'
│   │
│   ├── parsing/                # Regras para estruturar o texto em tabelas
│   │   ├── parser_espelho.py   # Extrator
│   │   └── criterios_gastro.py # Regras de Negócio do Gastro
│   │
│   ├── features/               # Engenharia de features
│   │   ├── feature_builder.py  # Limpeza Tabular
│   │   └── text_vectorization.py # NLP / TF-IDF
│   │
│   ├── models/                 # Treinamento e predição
│   │   ├── train_xgboost.py    # Script de treinamento
│   │   ├── evaluate_model.py   # Script de predição
│   │   └── inference.py        # Graficos
│   │
│   └── utils/                  # Funções auxiliares
│       ├── logger.py
│       └── file_utils.py
│
├── notebooks/
│   ├── 01_exploracao_dados.ipynb
│   ├── 02_limpeza_texto.ipynb
│   ├── 03_engenharia_features.ipynb
│   └── 04_modelagem.ipynb
│
├── models/
│   ├── xgboost_model.json      # Modelo treinado
│   └── vectorizers/            # TF-IDF / Embeddings
│
└── docs/
    ├── arquitetura_pipeline.png
    ├── criterios_regulacao.pdf
    └── relatorio_tecnico.pdf


PS. Alguns arquivos podem ainda não terem sidos criados por que ainda não chegamos na fase de desenvolvimento onde se faz necessário.


---

## 🚀 Como Rodar ao Adicionar Novos Dados (data/raw)

Sempre que eu colocar novos PDFs em `data/raw`, eu posso reprocessar a base com o pipeline de ingestão para atualizar o CSV consolidado em `data/processed/dataset_espelhos.csv`.

1) (Opcional) Criar e ativar ambiente virtual (Windows/PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Instalar dependências

```powershell
pip install -r requirements.txt
```

3) Executar o pipeline de ingestão

```powershell
python run_ingestion.py
```

- O arquivo de saída será sobrescrito: `data/processed/dataset_espelhos.csv`.
- Se um PDF não tiver texto (imagem escaneada), considerar realizar OCR antes de reprocessar (ver `src/extraction/ocr_utils.py`).
- Script responsável: [run_ingestion.py](run_ingestion.py)

---

## 🧪 Indicadores e Metas do Projeto

| Indicador | Meta |
|----------|------|
| **Acurácia do modelo** | ≥ 85% |
| **AUC-ROC** | ≥ 0,90 |
| **Redução do tempo de triagem (simulada)** | ≥ 40% |
| **Concordância pós-explicabilidade** | ≥ 70% |
| **Reencaminhamentos evitados (simulação)** | ≥ 50% |

---

## 🗓️ Cronograma Oficial (12 meses)

| Trimestre | Foco Principal | Produtos |
|----------|----------------|----------|
| **1º trimestre** | Estudos Teóricos + Engenharia de Dados Inicial | Dicionário de variáveis, base anonimizada inicial |
| **2º trimestre** | Pré-processamento + Análise Descritiva | Tabelas finais, gráficos, relatório exploratório |
| **3º trimestre** | Modelagem Preditiva | Modelos treinados + SHAP/LIME + relatório |
| **4º trimestre** | Protótipo + Simulações | Interface, testes retrospectivos, relatório final + resumo científico |

---

---

## 📘 Protocolo de Acesso e Regras do Modelo

O ARIS utiliza como referência o **Protocolo de Acesso da Gastro-Hepatologia (Enfermaria – HC-UFPE)**.  
Todo o processo de extração, parsing e modelagem se baseia nos seguintes componentes:

### ✔ Critérios de Aprovação (Elegibilidade)
São condições clínicas e diagnósticas que, quando presentes no espelho, **indicam forte aderência ao perfil da enfermaria**.  
Exemplos:

- Disfagia grave com perda ponderal  
- Diarreia crônica descompensada  
- Doença inflamatória intestinal refratária  
- Hepatites virais B e C agudas  
- Hepatite alcoólica aguda  
- Cirrose hepática descompensada  
- Investigação de tumores gastrointestinais  

### ❌ Critérios de Reprovação (Excludentes)
Têm prioridade sobre os critérios de aprovação.  
Se qualquer critério de reprovação aparecer, a solicitação deve ser recusada.

Exemplos:
  
- Hemorragia digestiva alta com indicação de EDA de urgência  
- Hepatite fulminante  
- Necessidade de suporte ventilatório  
- Necessidade de diálise  
- Neoplasia já definida com acompanhamento oncológico  
- COVID-19 (regra institucional)  

### ⚠ Regras Clínicas Especiais
- **COVID-19 → recusa imediata**  
- **Tuberculose → necessita avaliação humana (vaga de isolamento)**  
- **Neoplasia + quimioterapia → encaminhar para oncologia**  
- **Paciente interno do HC → tem prioridade regulatória**  

---

## 🗂️ Estrutura da Base de Dados (Schema)

A tabela abaixo descreve as colunas geradas no processo de parsing e utilizadas como features para treinamento do modelo.

| Feature | Tipo | Origem | Propósito |
|--------|------|--------|-----------|
| `Decisao_Final` | Categórica | Histórico do espelho | Variável alvo (Y) |
| `Idade` | Numérica | Cadastro | Critério ≥18 anos |
| `Diagnostico_Texto_Livre` | Texto | Justificativa médica | Input para NLP |
| `CID_10` | Categórica | Campo CID | Detecção de hepato/gastro específicas |
| `Sinais_Vitais_O2_Suporte` | Binário | Texto livre | Critério de reprovação |
| `Historico_Neoplasia_Onco` | Binário | Histórico | Critério de reprovação |
| `Necessidade_Dialise` | Binário | Texto livre | Critério de reprovação |
| `Necessidade_EDA_Urgencia` | Binário | Texto livre | Critério de reprovação |
| `Necessita_UTI_Potencial` | Binário | Texto livre | Gravidade extrema |
| `Exames_Corroboram_Suspeita` | Categórico | Observações | Conformidade documental |

O schema completo está em:  
📄 `docs/dicionario_variaveis.md`  
📄 `docs/metadata.md`

---


## ⚖️ Ética e Conformidade (LGPD e CNS 510/2016)

O ARIS segue integralmente:

- **LGPD (Lei nº 13.709/2018)**  
- **Resolução CNS nº 510/2016**  
- **PL 2.338/2023 (IA em saúde: alto risco)**  

Todos os dados utilizados são **anonimizados** previamente e manipulados em ambiente seguro.  
A IA é usada **exclusivamente como apoio à decisão**, sempre com supervisão humana.

---

## 👥 Equipe

- **Aluno Bolsista:** Gustavo Felipe Alves da Silva  
- **Orientador:** Prof. Fernando Moreira (HC-UFPE / Ebserh)  
- **Colaboradores:** Nara Cavalcanti 

---

## 📄 Publicações, Disseminação e Produtos Esperados
- Relatório técnico de Iniciação Tecnológica  
- Resumo científico para congressos  
- Protótipo funcional do ARIS  
- Artigo científico (dependendo dos resultados)  

---

Projeto: ARIS – Apoio Regulatório Inteligente em Saúde  
Instituição: HC-UFPE / Ebserh  

