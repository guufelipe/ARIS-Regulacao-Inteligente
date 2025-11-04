# 🏥 Projeto ARIS: Apoio Regulatório Inteligente em Saúde

## Visão Geral do Projeto

Este repositório contém os ativos e códigos do projeto **ARIS (Apoio Regulatório Inteligente em Saúde)**, uma iniciativa de Iniciação Tecnológica (PIT/Ebserh/CNPq) focada em aplicar Inteligência Artificial (IA) para aprimorar o processo de regulação interhospitalar no Sistema Único de Saúde (SUS).

O objetivo principal é desenvolver um protótipo de sistema capaz de analisar automaticamente os "espelhos de solicitação" de pacientes, prevendo a aderência ou não ao perfil regulatório do serviço de destino (HC-UFPE/Gastroenterologia).

---

## Foco e Metodologia (Fase Atual: Engenharia de Dados)

Estamos atualmente no **1º Trimestre** do projeto, focado na **Engenharia de Dados** e na **Arquitetura da Solução**, conforme a metodologia proposta:

1. **Mapeamento de Critérios:** Mapeamento detalhado dos protocolos de elegibilidade (Critérios de Aprovação e Reprovação) do setor de Gastroenterologia.
2.  **Extração de Dados:** Desenvolvimento de rotinas de pré-processamento para extrair dados estruturados a partir de documentos não estruturados (PDFs de espelhos de solicitação).
3.  **Estruturação da Base:** Criação da base de dados inicial (DataFrames) que servirá para o treinamento dos modelos preditivos na Fase 2.

## 📂 Estrutura do Repositório

O projeto está organizado nas seguintes pastas principais para garantir clareza e separação entre dados brutos e códigos:

| Pasta | Conteúdo Principal | Descrição e Propósito |

| **`code/`** | Notebooks Jupyter (`.ipynb`) e scripts Python. | Contém a lógica de extração, tratamento e as futuras fases de modelagem e validação. |
| **`code/planilhas_geradas/`** | Arquivos `.csv` e `.xlsx` gerados pelos Notebooks. | **Dados Estruturados:** Inclui as tabelas de regras (Critérios de Aprovação/Reprovação) e a tabela principal (`Solicitações_Espelhos_Brutos.csv`). |
| **`espelhos_pdf/`** | Documentos PDF originais. | Contém os **Dados Brutos (Input):** Protocolo de Acesso e os Espelhos de Solicitação/Regulação analisados, todos devidamente anonimizados. |

---

## Próximos Passos

Após a conclusão da Engenharia de Dados inicial, o foco será:

* **Engenharia de Features:** Criação de *flags* binárias e variáveis numéricas a partir do texto livre e dos sinais vitais.
* **Modelagem Preditiva:** Treinamento de modelos de IA supervisionada (e.g., Random Forest, XGBoost) para prever a aderência ao perfil regulatório.

---

## Equipe e Instituições

* **Aluno Bolsista (IC/PIT):** Gustavo Felipe Alves Da Silva
* **Orientador:** Fernando José Moreira de Oliveira Júnior
* **Projeto:** ARIS: Apoio Regulatório Inteligente em Saúde
* **Programa:** Programa de Iniciação Tecnológica (PIT Ebserh/CNPq)

---

## ⚖️ Conformidade Legal e Ética

Este projeto é desenvolvido em estrita conformidade com a **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018)** e a **Resolução CNS nº 510/2016**. [cite_start]Todos os dados são previamente anonimizados, e a IA é utilizada estritamente como um sistema de apoio à decisão, sob supervisão humana contínua.