# 🧾 Metadados da Base — ARIS
**Versão:** 2.0  
**Última atualização:** 2025-12  

Este documento descreve **como os dados brutos (espelhos de solicitação)** são transformados em dados estruturados utilizados para treinamento e teste dos modelos de IA do projeto ARIS.

---

# 1. Origem dos Dados

- **Fonte primária:** Espelhos de Solicitação da Central de Regulação Hospitalar.  
- **Formato original:** PDF (nativo ou digitalizado).  
- **Quantidade inicial:** 20 documentos.  
- **Formato após extração:** JSON estruturado, CSV e Parquet.  
- **Processamento inicial:** scripts Python com `pdfplumber`, `regex`, e pré-processamento NLP.

### Blocos que compõem cada espelho:
1. **Identificação do Estabelecimento**
2. **Identificação do Paciente**
3. **Dados da Solicitação**
4. **Justificativa / Quadro Clínico (Texto Livre)**
5. **Principais Exames e Resultados**
6. **CID Principal e Secundário**
7. **Sinais Vitais**
8. **Evolução / Observações**
9. **Processo Regulatório (linha do tempo)**
10. **Autorização**
11. **Comunicação Ativa**
12. **Procedimento Solicitado**
13. **Transferência e Observações**

Essas seções variam entre hospitais, e muitos campos podem vir vazios.

---

# 2. Estrutura Técnica dos Arquivos Extraídos

- **Formato final recomendado:**  
  - `data/processed/solicitacoes.parquet` (base treinável)  
  - `data/raw/espelhos/*.pdf` (originais)  
  - `data/intermediate/*.json` (saída do parser)

- **Encoding:** UTF-8  
- **Delimitador:** `,` (para CSV)  
- **Separação de feature sets:**
  - `features_textuais` → provenientes do texto livre
  - `features_categóricas` → campos estruturados do PDF
  - `features_binárias` → flags baseadas em regras clínicas
  - `label` → decisão final (Aprovado / Reprovado / Regulou)

---

# 3. Esquema da Tabela Final (Schema da Base Treinável)

A tabela final é sempre construída com um registro por solicitação.  
A seguir estão todas as variáveis, **com a origem real no espelho**.

---

## 3.1 Variáveis de Identificação (não utilizadas no modelo)

| Variável | Tipo | Origem | Status |
|----------|------|--------|--------|
| `id_solicitacao` | string | Nº da solicitação | Usado só para rastreio |
| `estabelecimento_solicitante` | string | Cabeçalho | Removido no treino |
| `data_solicitacao` | data | Cabeçalho | Removido no treino |
| `sexo` | categórico | Identificação | Pode ser usada se necessário |

Todos esses campos são mantidos apenas para auditoria.

---

## 3.2 Variáveis Clínicas Estruturadas

| Variável | Tipo | Origem no Espelho |
|----------|------|-------------------|
| `idade` | numérico | Linha “IDADE: xx anos” |
| `diagnostico_inicial` | texto | Campo “Diagnóstico Inicial” |
| `cid_principal` | categórico | Campo “CID PRINCIPAL” |
| `cid_secundario` | categórico | Campo “CID SECUNDÁRIO” |
| `resultados_exames` | texto | Campo “PRINCIPAIS RESULTADOS DE PROVAS DIAGNÓSTICAS” |
| `sinais_vitais_fc` | numérico | “F. CARDÍACA” |
| `sinais_vitais_fr` | numérico | “F. RESPIRATÓRIA” |
| `sinais_vitais_saturacao` | numérico | “SATURACAO” |
| `sinais_vitais_sup_ox` | binário | “SUP O₂” |
| `localizacao` | categórico | Campo “LOCALIZAÇÃO: Vermelha/Amarela/etc.” |

---

## 3.3 Variáveis Textuais (usadas em NLP)

| Variável | Origem | Observações |
|----------|--------|-------------|
| `quadro_clinico_texto` | Quadro Clínico / Sinais e Sintomas | Texto livre principal do caso |
| `evolucao_texto` | Seção EVOLUÇÃO | Pode conter info de gravidade |
| `observacoes_solicitacao` | Campo “OBSERVAÇÃO DA SOLICITAÇÃO” | Texto curto |
| `comunicacao_ativa` | Comunicação Ativa → Descrição | Auxilia no contexto regulatório |

Isa variável é geralmente concatenada em um único texto:

texto_unificado = quadro_clinico_texto + evolucao_texto + exames + observações



---

## 3.4 Variáveis Binárias Derivadas (Rules → Flags)

Baseadas nos critérios de aprovação/reprovação.

| Flag | Regra | Origem |
|------|-------|--------|
| `flag_suporte_oxigenio` | “SUP O₂ > 0” | Sinais vitais |
| `flag_necessidade_dialise` | palavras-chave | Texto livre |
| `flag_disfuncao_hepatica_grave` | presença de encefalopatia, ascite tensa, icterícia marcada | Texto |
| `flag_doenca_hepatica_clara` | presença de “cirrose”, “DHC”, “hepatite”, “esteato hepática” | Texto |
| `flag_condicao_excludente` | hepatite fulminante, neoplasia avançada, ventilação mecânica etc. | Texto |
| `flag_caso_ambulatorial` | texto indicando acompanhamento no HC | Texto |
| `flag_covid` | presença de COVID | Texto |

---

## 3.5 Variável Alvo (Label)

| Variável | Valores | Origem |
|----------|---------|--------|
| `decisao_final` | {Aprovado, Reprovado, Regulou, Alta, Cancelado} | Processo Regulatório / Autorização |

Para o modelo inicial, reduzimos para:

- **1 = Regulou/Aprovado**
- **0 = Não regulou / Reprovado / Cancelado**

---

# 4. Processamento Aplicado

### 4.1 Extração do PDF
- Ferramenta: `pdfplumber`
- Normalização:
  - remoção de quebras de linha
  - remoção de símbolos da conversão PDF
  - reconstrução de frases quebradas
  - extração de blocos por heurística

### 4.2 Estruturação
- Regex para:
  - idade
  - localização
  - sinais vitais
  - CID
  - diagnóstico inicial
- Identificação de seções por marcadores fixos:
  - “JUSTIFICATIVA”
  - “PRINCIPAIS RESULTADOS”
  - “EVOLUÇÃO”
  - “TEMPO DE ATENDIMENTO”
  - “AUTORIZAÇÃO”

### 4.3 Vetorização
- Textual:
  - TF-IDF (baseline)
  - BERTimbau / ClinicalBERT (futuro)
- Numérica:
  - MinMaxScaler
- Categórica:
  - OneHotEncoder

---

# 5. Metadados de Qualidade e LGPD

- **Anonimização prévia** garantida pela colaboradora NARA.
- Ausência de CPF, nome, CNS e endereço (todos removidos).
- Riscos de reidentificação: baixo.
- Base usada exclusivamente para pesquisa, sob Comitê de Ética e LGPD.
- Armazenamento local seguro, sem cloud pública.


