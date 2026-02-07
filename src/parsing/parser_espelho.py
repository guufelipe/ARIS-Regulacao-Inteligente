import re
from src.extraction.text_cleaner import clean_bad_encoding
from src.parsing.criterios_gastro import (
    TERMOS_EXCLUSAO,
    TERMOS_INCLUSAO,
    verificar_criterio
)


def remover_dados_sensiveis(texto):
    """
    Remove possíveis dados sensíveis do texto clínico.
    Estratégia conservadora para evitar vazamento de identidade.
    """

    if not texto:
        return texto

    # Remove linhas explícitas de identificação
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

    # Remove possíveis nomes próprios (duas ou mais palavras capitalizadas)
    texto_limpo = re.sub(
        r'\b[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+\s+[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõ]+\b',
        '',
        texto_limpo
    )

    return texto_limpo.strip()


def extrair_bloco(texto, inicio, fim=None, limite=1200):
    """
    Extrai um bloco de texto entre âncoras semânticas.
    """
    if fim:
        padrao = f'{inicio}.*?[:\-](.*?){fim}'
    else:
        padrao = f'{inicio}.*?[:\-](.*)'

    match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(1).strip()[:limite]

    return None


def parse_text_to_dict(texto_bruto):
    """
    Parser clínico com foco em:
    - Privacidade do paciente
    - Extração semântica por blocos
    - Geração de flags clínicas atômicas
    """

    dados = {}

    # =========================================================================
    # 1. LIMPEZA E NORMALIZAÇÃO
    # =========================================================================

    texto_decodificado = clean_bad_encoding(texto_bruto)
    texto_limpo = " ".join(texto_decodificado.split())
    texto_lower = texto_limpo.lower()

    # =========================================================================
    # 2. IDENTIFICAÇÃO DO PACIENTE (APENAS IDADE E SEXO)
    # =========================================================================

    match_idade = re.search(r'IDADE[:\-]?\s*(\d{1,3})', texto_limpo, re.IGNORECASE)
    dados['Idade'] = int(match_idade.group(1)) if match_idade else None

    match_sexo = re.search(r'SEXO[:\-]?\s*(\w+)', texto_limpo, re.IGNORECASE)
    dados['Sexo'] = match_sexo.group(1).upper() if match_sexo else "N/I"

    # =========================================================================
    # 3. JUSTIFICATIVA DE INTERNAÇÃO (COM HIGIENIZAÇÃO)
    # =========================================================================

    justificativa = extrair_bloco(
        texto_limpo,
        inicio=r'JUSTIFICATIVA DE INTERNAÇÃO',
        fim=r'(EVOLUÇÃO|SINAIS VITAIS|EXAMES|CONDUTA)'
    )

    dados['Justificativa_Internacao'] = remover_dados_sensiveis(justificativa)

    # =========================================================================
    # 4. EVOLUÇÃO CLÍNICA
    # =========================================================================

    evolucao = extrair_bloco(
        texto_limpo,
        inicio=r'EVOLUÇÃO',
        fim=r'(SINAIS VITAIS|EXAMES|CONDUTA)'
    )

    dados['Evolucao'] = remover_dados_sensiveis(evolucao)

    # =========================================================================
    # 5. SINAIS VITAIS (TEXTO COMPLETO)
    # =========================================================================

    sinais_vitais = extrair_bloco(
        texto_limpo,
        inicio=r'SINAIS VITAIS',
        fim=r'(EXAMES|CONDUTA)'
    )

    dados['Sinais_Vitais_Texto'] = sinais_vitais

    # =========================================================================
    # 6. FLAGS CLÍNICAS ATÔMICAS (SEM DECISÃO)
    # =========================================================================

    flags_exclusao = {
        chave: verificar_criterio(texto_lower, termos)
        for chave, termos in TERMOS_EXCLUSAO.items()
    }

    flags_inclusao = {
        chave: verificar_criterio(texto_lower, termos)
        for chave, termos in TERMOS_INCLUSAO.items()
    }

    dados['flags_exclusao'] = flags_exclusao
    dados['flags_inclusao'] = flags_inclusao

    return dados
