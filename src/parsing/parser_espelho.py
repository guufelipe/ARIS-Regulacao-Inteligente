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

    padrao = rf'({inicio_regex})\s*[:\-]?\s*(.*?)(?=\n\s*({fim_regex})\b|\Z)'
    match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(2).strip()[:limite]

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
    # 3. JUSTIFICATIVA DE INTERNAÇÃO (CAMPO TEXTUAL PRINCIPAL)
    # -------------------------------------------------------------------------

    justificativa = extrair_bloco_por_titulo(
        texto,
        titulos_inicio=[
            "JUSTIFICATIVA DA INTERNAÇÃO"
        ],
        titulos_fim=[
            "EVOLUÇÃO",
            "SINAIS VITAIS",
            "EXAMES",
            "CONDUTA"
        ]
    )

    dados["Justificativa_Internacao"] = remover_dados_sensiveis(justificativa)

    # -------------------------------------------------------------------------
    # 4. EVOLUÇÃO CLÍNICA
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
    # 5. CID (QUANDO EXPLÍCITO)
    # -------------------------------------------------------------------------

    match_cid = re.search(r'\bCID[\s\-:]?\s*([A-Z]\d{2}(\.\d+)?)', texto)
    dados["CID_10"] = match_cid.group(1) if match_cid else None

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
