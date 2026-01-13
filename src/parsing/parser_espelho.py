import re
from src.extraction.text_cleaner import clean_bad_encoding
# Importamos as regras oficiais do protocolo
from src.parsing.criterios_gastro import TERMOS_EXCLUSAO, TERMOS_INCLUSAO, verificar_criterio

def parse_text_to_dict(texto_bruto):
    dados = {}
    
    # 1. Limpeza e Decodificação
    texto_decodificado = clean_bad_encoding(texto_bruto)
    texto_limpo = " ".join(texto_decodificado.split())
    # Normalização para busca de termos
    texto_lower = texto_limpo.lower()

    # --- EXTRAÇÃO INTELIGENTE DE IDADE ---
    match_idade_header = re.search(r'IDADE[:ś]?\s*(\d{1,3})', texto_limpo, re.IGNORECASE)
    idade_header = int(match_idade_header.group(1)) if match_idade_header else None

    match_idade_texto = re.search(r'(?:PACIENTE|ID)[:,\s]+(\d{1,3})\s*(?:ANOS|A\b)', texto_limpo, re.IGNORECASE)
    idade_texto = int(match_idade_texto.group(1)) if match_idade_texto else None

    if idade_texto and (idade_header is None or idade_header < 18):
        dados['Idade'] = idade_texto
    elif idade_header:
        dados['Idade'] = idade_header
    else:
        dados['Idade'] = None

    # --- SEXO ---
    match_sexo = re.search(r'SEXO[:ś]?\s*(\w+)', texto_limpo, re.IGNORECASE)
    dados['Sexo'] = match_sexo.group(1).upper() if match_sexo else "N/I"

    # --- EXTRAÇÃO DO TEXTO CLÍNICO ---
    inicio = r'(?:QUADRO CLÍNICO|SINAIS E SINTOMAS|HISTÓRIA DA DOENÇA|RESUMO)'
    fim = r'(?:CONDIÇÕES QUE JUSTIFIQUEM|PRINCIPAIS RESULTADOS|DIAGNÓSTICO INICIAL|HDA:)'
    padrao = f'{inicio}.*?[:ś/-](.*?){fim}'
    
    match_diag = re.search(padrao, texto_limpo, re.IGNORECASE)
    if match_diag:
        dados['Diagnostico_Texto_Livre'] = match_diag.group(1).strip()
    else:
        fallback = re.search(r'(?:SINAIS E SINTOMAS|QUADRO CLÍNICO)[:ś]?(.*)', texto_limpo, re.IGNORECASE)
        dados['Diagnostico_Texto_Livre'] = fallback.group(1)[:800].strip() if fallback else "TEXTO NÃO ENCONTRADO"

    # =========================================================================
    # ENGENHARIA DE FEATURES (FLAGS MÉDICAS)
    # Aqui usamos as regras do Protocolo Oficial (criterios_gastro.py)
    # =========================================================================
    
    # 1. Critérios de EXCLUSÃO (Flags de Risco)
    dados['Necessidade_Dialise'] = verificar_criterio(texto_lower, TERMOS_EXCLUSAO['nefrologia_dialise'])
    dados['Instabilidade_Hemodinamica'] = verificar_criterio(texto_lower, TERMOS_EXCLUSAO['instabilidade_grave'])
    dados['Hemorragia_Ativa'] = verificar_criterio(texto_lower, TERMOS_EXCLUSAO['hemorragia_urgencia'])
    dados['Suspeita_Infecciosa'] = verificar_criterio(texto_lower, TERMOS_EXCLUSAO['doencas_infectocontagiosas'])
    dados['Oncologia_Fora_Perfil'] = verificar_criterio(texto_lower, TERMOS_EXCLUSAO['oncologia_definida'])

    # Lógica mista para Suporte O2 (Regex numérico + Termos do protocolo)
    match_o2 = re.findall(r'SUP 02[:ś]?\s*(\d+)', texto_limpo, re.IGNORECASE)
    valores_o2 = [int(v) for v in match_o2]
    max_o2 = max(valores_o2) if valores_o2 else 0
    uso_resp_texto = verificar_criterio(texto_lower, TERMOS_EXCLUSAO['suporte_ventilatorio'])
    
    dados['Sinais_Vitais_O2_Suporte'] = 1 if (max_o2 > 0 or uso_resp_texto) else 0

    # 2. Critérios de INCLUSÃO (Perfil Gastro)
    # Agrupamos várias subcategorias em uma flag forte "Tem_Perfil_Gastro"
    tem_hepato = verificar_criterio(texto_lower, TERMOS_INCLUSAO['hepatopatia_descompensada'])
    tem_dii = verificar_criterio(texto_lower, TERMOS_INCLUSAO['doencas_inflamatorias'])
    tem_investigacao = verificar_criterio(texto_lower, TERMOS_INCLUSAO['investigacao_neoplasia'])
    tem_colestase = verificar_criterio(texto_lower, TERMOS_INCLUSAO['colestase'])
    
    dados['Sinais_Gastro_Hepato'] = 1 if (tem_hepato or tem_dii or tem_investigacao or tem_colestase) else 0

    # --- CID ---
    match_cid = re.search(r'CID PRINCIPAL[:ś]?\s*([A-Z]\d+)', texto_limpo, re.IGNORECASE)
    dados['CID_10'] = match_cid.group(1) if match_cid else "N/I"

    return dados