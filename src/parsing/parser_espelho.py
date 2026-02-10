import re

from src.extraction.text_cleaner import clean_bad_encoding
from src.parsing.criterios_gastro import (
    TERMOS_EXCLUSAO,
    TERMOS_INCLUSAO,
    verificar_criterio
)

# =============================================================================
# UTILITÁRIOS DE PRIVACIDADE
# =============================================================================

def remover_dados_sensiveis(texto: str | None) -> str | None:
    if not texto:
        return None

    padroes_sensiveis = [
        r'nome\s*[:\-].*',
        r'endere[cç]o\s*[:\-].*',
        r'rua\s+[\w\s]+',
        r'avenida\s+[\w\s]+',
        r'bairro\s+[\w\s]+',
        r'cep\s*\d+',
        r'cpf\s*\d+',
        r'rg\s*\d+'
    ]

    texto_limpo = texto
    for padrao in padroes_sensiveis:
        texto_limpo = re.sub(padrao, '', texto_limpo, flags=re.IGNORECASE)

    texto_limpo = re.sub(
        r'\b[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+\b',
        '',
        texto_limpo
    )

    return texto_limpo.strip()


# =============================================================================
# NORMALIZAÇÃO E EXTRAÇÃO POR BLOCOS
# =============================================================================

def normalizar_texto(texto: str) -> str:
    texto = clean_bad_encoding(texto)
    texto = texto.replace("\r", "\n")
    texto = re.sub(r'\n{2,}', '\n', texto)
    return texto.strip()


def extrair_bloco_por_titulo(
    texto: str,
    titulos_inicio: list[str],
    titulos_fim: list[str],
    limite: int = 4000
) -> str | None:
    if not texto:
        return None

    inicio_regex = "|".join(titulos_inicio)
    fim_regex = "|".join(titulos_fim)

    # Ajuste: flags=re.IGNORECASE já garante que pegue maiúsculas/minúsculas
    padrao = rf'({inicio_regex})\s*[:\-]?\s*(.*?)(?=\n\s*({fim_regex})\b|\Z)'
    match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(2).strip()[:limite]

    return None

# Nova função auxiliar para extrair subcampos de Sinais Vitais
def extrair_sinais_vitais(texto_bloco: str | None) -> dict:
    sv_dados = {
        "G_TDR": None,
        "F_Cardiaca": None,
        "F_Respiratoria": None,
        "Saturacao": None,
        "Sup_O2": None
    }
    
    if not texto_bloco:
        return sv_dados

    # Regex para capturar valores numéricos ou descritivos curtos após os rótulos
    # Aceita formatos como "100 bpm", "100", "98%"
    
    # G-TDR (Glicemia)
    match_gtdr = re.search(r'G[- ]?TDR\s*[:\-]?\s*([\w\d]+)', texto_bloco, re.IGNORECASE)
    if match_gtdr: sv_dados["G_TDR"] = match_gtdr.group(1)

    # F. Cardíaca
    match_fc = re.search(r'F\.?\s*CARD[IÍ]ACA\s*[:\-]?\s*(\d+)', texto_bloco, re.IGNORECASE)
    if match_fc: sv_dados["F_Cardiaca"] = match_fc.group(1)

    # F. Respiratória
    match_fr = re.search(r'F\.?\s*RESPIRAT[OÓ]RIA\s*[:\-]?\s*(\d+)', texto_bloco, re.IGNORECASE)
    if match_fr: sv_dados["F_Respiratoria"] = match_fr.group(1)

    # Saturação
    match_sat = re.search(r'SATURACAO\s*[:\-]?\s*(\d+%?)', texto_bloco, re.IGNORECASE)
    if match_sat: sv_dados["Saturacao"] = match_sat.group(1)

    # Sup O2
    match_sup = re.search(r'SUP\s*O2\s*[:\-]?\s*([^\n,;]+)', texto_bloco, re.IGNORECASE)
    if match_sup: sv_dados["Sup_O2"] = match_sup.group(1).strip()

    return sv_dados


# =============================================================================
# FUNÇÃO ESPECIALIZADA PARA CID (ROBUSTA)
# =============================================================================

def extrair_cid_robusto(texto: str | None) -> str | None:
    if not texto:
        return None
    
    # 1. Regex Tolerante:
    # \bCID\s* -> Encontra a palavra CID
    # (?:PRINCIPAL)?\s* -> Opcionalmente encontra PRINCIPAL
    # [^A-Z0-9\n]* -> O TRUQUE: Consome qualquer caractere que NÃO seja
    #                              letra maiúscula, número ou quebra de linha.
    #                              Isso engole ':', 'ś', '-', espaços, lixo de encoding.
    # ([^\s\n]+)                -> Captura o próximo bloco de texto (o candidato a código)
    
    padrao_captura = r'\bCID\s*(?:PRINCIPAL)?\s*[^A-Z0-9\n]*([^\s\n]+)'
    
    match = re.search(padrao_captura, texto, re.IGNORECASE)
    
    if match:
        candidato_sujo = match.group(1) # Ex: Pega "Rɭɥɨ" ou "A09"
        
        # 2. Limpeza Pós-Captura (como solicitado)
        candidato_limpo = clean_bad_encoding(candidato_sujo)
        
        # 3. Validação Final
        # Tenta encontrar o padrão de CID (Letra + 2/3 digitos) dentro do candidato limpo
        match_validacao = re.search(r'([A-Z]\d{2}(?:\.\d+)?)', candidato_limpo, re.IGNORECASE)
        
        if match_validacao:
            return match_validacao.group(1).upper()
            
    return None

# =============================================================================
# PARSER PRINCIPAL
# =============================================================================

def parse_text_to_dict(texto_bruto: str) -> dict:
    dados: dict = {}

    # -------------------------------------------------------------------------
    # 1. LIMPEZA E NORMALIZAÇÃO
    # -------------------------------------------------------------------------

    texto = normalizar_texto(texto_bruto)
    texto_lower = texto.lower()

    # -------------------------------------------------------------------------
    # 2. IDENTIFICAÇÃO BÁSICA
    # -------------------------------------------------------------------------

    match_idade = re.search(r'idade\s*[:\-]?\s*(\d{1,3})', texto, re.IGNORECASE)
    dados["Idade"] = int(match_idade.group(1)) if match_idade else None

    match_sexo = re.search(
        r'sexo\s*[:\-]?\s*(masculino|feminino|m|f)',
        texto,
        re.IGNORECASE
    )
    dados["Sexo"] = match_sexo.group(1).upper()[0] if match_sexo else "N/I"

    # -------------------------------------------------------------------------
    # 3. JUSTIFICATIVA DE INTERNAÇÃO & CID PRINCIPAL
    # -------------------------------------------------------------------------

    justificativa = extrair_bloco_por_titulo(
        texto,
        titulos_inicio=[
            "JUSTIFICATIVA DA INTERNAÇÃO",
            "JUSTIFICATIVA"
        ],
        titulos_fim=[
            "EVOLUÇÃO",
            "SINAIS VITAIS",
            "EXAMES",
            "CONDUTA"
        ]
    )

    # Tenta extrair primeiro da Justificativa (Prioridade)
    cid_encontrado = extrair_cid_robusto(justificativa)
    
    # Fallback: Se não achou na justificativa, tenta no texto inteiro
    # (Útil caso o CID esteja solto no cabeçalho ou fora de ordem)
    if not cid_encontrado:
        cid_encontrado = extrair_cid_robusto(texto)

    dados["CID_10"] = cid_encontrado
    dados["Justificativa_Internacao"] = remover_dados_sensiveis(justificativa)

    dados["CID_10"] = cid_encontrado
    dados["Justificativa_Internacao"] = remover_dados_sensiveis(justificativa)

    # -------------------------------------------------------------------------
    # 4. SINAIS VITAIS (NOVA LÓGICA)
    # -------------------------------------------------------------------------

    bloco_sinais = extrair_bloco_por_titulo(
        texto,
        titulos_inicio=["SINAIS VITAIS"],
        titulos_fim=["HISTÓRICO PSIQUIÁTRICO", 'EXECUTANTE']
    )
    
    # Extrai os subcampos
    dados_sv = extrair_sinais_vitais(bloco_sinais)

    # Flag geral: existem sinais vitais?
    dados["Sinais_Vitais"] = dados_sv

    
    # Se quiser manter o texto bruto dos sinais vitais para auditoria:
    # dados["Sinais_Vitais_Texto"] = bloco_sinais 

    print("=== BLOCO SINAIS VITAIS ===")
    print(bloco_sinais)
    print("=== DADOS EXTRAÍDOS ===")
    print(dados_sv)


    # -------------------------------------------------------------------------
    # 5. EVOLUÇÃO CLÍNICA
    # -------------------------------------------------------------------------

    evolucao = extrair_bloco_por_titulo(
        texto,
        titulos_inicio=[
            "EVOLUÇÃO",
            "EVOLUÇÃO CLÍNICA"
        ],
        titulos_fim=[
            "SINAIS VITAIS",
            "EXAMES",
            "CONDUTA"
        ]
    )

    dados["Evolucao"] = remover_dados_sensiveis(evolucao)

    # -------------------------------------------------------------------------
    # 6. FLAGS CLÍNICAS (REGRAS DE NEGÓCIO — INTACTAS)
    # -------------------------------------------------------------------------

    flags_exclusao = {
        chave: verificar_criterio(texto_lower, termos)
        for chave, termos in TERMOS_EXCLUSAO.items()
    }

    flags_inclusao = {
        chave: verificar_criterio(texto_lower, termos)
        for chave, termos in TERMOS_INCLUSAO.items()
    }

    dados["Necessidade_Dialise"] = flags_exclusao.get("nefrologia_dialise", 0)
    # Nota: Mantive a flag antiga de O2, mas agora você tem também o dado "Sup_O2" extraído acima
    dados["Sinais_Vitais_O2_Suporte"] = flags_exclusao.get("suporte_ventilatorio", 0)
    dados["Instabilidade_Hemodinamica"] = flags_exclusao.get("instabilidade_grave", 0)

    dados["Hemorragia_Ativa"] = verificar_criterio(
        texto_lower,
        ["hemorragia", "sangramento", "melena", "hematêmese", "fezes sanguinolentas"]
    )

    dados["Suspeita_Infecciosa"] = verificar_criterio(
        texto_lower,
        ["infecção", "sepse", "séptico", "febre persistente"]
    )

    dados["Oncologia_Fora_Perfil"] = flags_exclusao.get("oncologia_fora_perfil", 0)
    dados["Sinais_Gastro_Hepato"] = flags_inclusao.get("hepatopatia_descompensada", 0)

    return dados    