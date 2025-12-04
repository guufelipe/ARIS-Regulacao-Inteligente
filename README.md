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
│   ├── interim/                # Textos extraídos, JSON, resultados intermediários
│   └── processed/              # DataFrames finais prontos para modelagem (CSV/Parquet)
│
├── src/
│   ├── extraction/             # Módulos de extração de texto dos PDFs
│   │   ├── pdf_extractor.py
│   │   ├── text_cleaner.py
│   │   └── ocr_utils.py
│   │
│   ├── parsing/                # Regras para estruturar o texto em tabelas
│   │   ├── parser_espelho.py
│   │   └── criterios_gastro.py
│   │
│   ├── features/               # Engenharia de features
│   │   ├── feature_builder.py
│   │   └── text_vectorization.py
│   │
│   ├── models/                 # Treinamento e predição
│   │   ├── train_xgboost.py
│   │   ├── evaluate_model.py
│   │   └── inference.py
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

