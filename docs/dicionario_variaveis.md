# 📘 Dicionário de Variáveis — Projeto ARIS

Este documento descreve cada variável utilizada na base estruturada do projeto ARIS, incluindo:

- Definição  
- Tipo  
- Origem no PDF  
- Transformações aplicadas  
- Possíveis valores  
- Observações clínicas e técnicas  

---

# 1. Variáveis de Identificação (não utilizadas no modelo)

| Nome | Tipo | Origem no PDF | Observações |
|------|------|----------------|-------------|
| `id_solicitacao` | string | Cabeçalho (“Solicitação nº”) | Usado apenas para auditoria |
| `estabelecimento_solicitante` | string | Cabeçalho | Não entra no treino |
| `data_solicitacao` | data | Cabeçalho | Pode indicar sazonalidade, mas não será usada inicialmente |
| `sexo` | categórica | Campo “SEXO” | Opcional no modelo |
| `municipio_origem` | string | Campo “MUN ORIGEM” | Não usado no modelo |

---

# 2. Variáveis Clínicas Estruturadas

| Variável | Tipo | Origem Real no PDF | Descrição / Observações |
|----------|------|---------------------|--------------------------|
| `idade` | numérico | Linha “IDADE: xx anos” | Usada para checar critérios ≥18 anos |
| `diagnostico_inicial` | texto | Campo “DIAGNÓSTICO INICIAL” | Pode ser curto ou apenas "não informado" |
| `cid_principal` | categórico | Campo “CID PRINCIPAL” | Nem sempre preenchido |
| `cid_secundario` | categórico | Campo “CID SECUNDÁRIO” | Quase sempre vazio |
| `localizacao` | categórico | Campo “LOCALIZAÇÃO: Vermelha/Amarela/etc.” | Indica gravidade |
| `resultados_exames` | texto | Campo “PRINCIPAIS RESULTADOS DE PROVAS DIAGNÓSTICAS” | Pode conter exames laboratoriais ou de imagem |
| `sinais_vitais_fc` | numérico | Campo “F. CARDÍACA” | Falta de preenchimento é comum |
| `sinais_vitais_fr` | numérico | Campo “F. RESPIRATÓRIA” | Pode vir como texto |
| `sinais_vitais_saturacao` | numérico | Campo “SATURAÇÃO” | Valores abaixo de 92% indicam gravidade |
| `sinais_vitais_sup_ox` | categórico (Sim/Não) | Campo “SUP O₂” | Se >0 = suporte O₂ |

---

# 3. Variáveis Textuais (para NLP)

Essas variáveis são extraídas como texto livre usando técnicas de segmentação e regex.

| Variável | Origem no PDF | Observações |
|----------|----------------|-------------|
| `quadro_clinico_texto` | Campo “QUADRO CLÍNICO / SINAIS E SINTOMAS” | Texto principal do caso |
| `evolucao_texto` | Campo “EVOLUÇÃO” | Importante para identificar descompensação |
| `observacoes_solicitacao` | Campo “OBSERVAÇÕES DA SOLICITAÇÃO” | Em geral contém informações logísticas |
| `comunicacao_ativa_texto` | Campo “COMUNICAÇÃO ATIVA → Observações” | Pode indicar urgência, pendências e reavaliações |
| `texto_unificado` | Concatenação das anteriores | Alimenta TF-IDF/BERT |

---

# 4. Variáveis Regulátorias (Processo)

| Variável | Tipo | Origem | Observações |
|----------|-------|--------|-------------|
| `tempo_espera` | numérico (minutos/hours) | Cálculo: solicitação → autorização | Nem sempre o campo está completo |
| `tipo_procedimento_solicitado` | categórica | Campo “PROCEDIMENTO SOLICITADO” | Geralmente “Internação Clínico-Geral” |
| `prioridade` | categórica | “Vermelha / Amarela / Verde” | Derivado de `localizacao` |

---

# 5. Flags Clínicas (Derivadas automaticamente)

Estas são variáveis criadas por regras baseadas em texto e/ou campos estruturados.  
São fundamentais para o modelo e refletem diretamente o **protocolo clínico da Gastro-Hepatologia**.

| Variável | Tipo | Regra de Derivação | Racional Regulatório |
|----------|------|---------------------|-----------------------|
| `flag_suporte_oxigenio` | binária | `sup_ox > 0` | Indica necessidade de suporte ventilatório → reprovação |
| `flag_dispneia` | binária | busca por “dispneia”, “dificuldade respirar” | Gravidade respiratória |
| `flag_necessidade_dialise` | binária | palavras-chave: “hemodiálise”, “IRA dialítica” | Contraindicação ao perfil enfermaria |
| `flag_neoplasia_em_tratamento` | binária | termos: “quimioterapia”, “radioterapia”, “oncologia” | Encaminhar para oncologia |
| `flag_hepatopatia_grave` | binária | “cirrose”, “DHC”, “encefalopatia”, “ascite tensa” | Critério forte |
| `flag_tuberculose` | binária | “TB”, “TBC”, “tuberculose” | Precisa de leito de isolamento → pendência |
| `flag_covid` | binária | “COVID”, “SARS-CoV-2” | Reprovação direta |
| `flag_hemorragia_digestiva` | binária | termos: “HDA”, “hemorragia digestiva” | Se com urgência → reprovação |
| `flag_hepatite_fulminante` | binária | “fulminante” | Requer UTI |
| `flag_investigacao_gastro` | binária | tumores GI, DII, disfagia grave | Critério favorável |
| `flag_conforme_protocolo` | binária | combinação dos critérios de aprovação | Avaliação global |

---

# 6. Variável Alvo (Label)

| Nome | Valores | Descrição |
|------|---------|-----------|
| `decisao_final` | `1 = Regulou/Aprovado`, `0 = Não Regulou/Reprovado/Cancelado` | Variável a ser prevista pelo modelo |

---

# 7. Glossário de Termos Clínicos (usado pelo parser NLP)

### Termos que indicam aprovação (Gastro/Hepato)
- “DII”, “doença inflamatória intestinal”
- “disfagia + perda ponderal”
- “tumor gastrointestinal”
- “cirrose descompensada”
- “ascite”, “encefalopatia hepática”
- “hepatite viral aguda”
- “nódulo hepático”

### Termos que indicam reprovação
- “hepatite fulminante”
- “hemodiálise”, “diálise”
- “COVID”, “SARS-CoV-2”
- “neoplasia com quimioterapia”
- “HDA com urgência”
- “ventilação mecânica”

---

# 8. Transformações Aplicadas (para machine learning)

| Tipo | Descrição |
|------|-----------|
| Padronização de texto | lowercase, remoção de stopwords, acentos |
| Regex | extração de idade, sinais vitais, CID |
| Vetorização | TF-IDF (baseline), BERT (futuro) |
| Normalização numérica | MinMaxScaler |
| Codificação categórica | OneHotEncoder |
| Imputação | Estratégia: `missing → NaN` ou `0` (flags) |

---

# 9. Observações Gerais

- Muitos campos vêm vazios → é esperado.  
- Texto médico pode conter abreviações: TB, DII, HDA, DHC.  
- A base final tem natureza **semi-estruturada**: mistura texto, números e categorias.  
- Flags clínicas são essenciais para reduzir ruído dos textos.

