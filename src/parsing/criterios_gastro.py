"""
Módulo de Inteligência Médica do ARIS - GASTRO-HEPATOLOGIA.

Este módulo centraliza TODA a lógica clínica baseada no
Protocolo Oficial de Acesso (HC-UFPE).

Responsabilidades:
- Definir vocabulário médico oficial (termos de inclusão e exclusão)
- Detectar evidências clínicas no texto
- Agregar decisões clínicas (exclusão, perfil gastro, elegibilidade)

IMPORTANTE:
Este módulo NÃO faz parsing de texto bruto.
Ele opera sobre texto já normalizado (lowercase).
"""


# ==============================================================================
# FUNÇÕES BÁSICAS DE DETECÇÃO SEMÂNTICA
# ==============================================================================

def verificar_criterio(texto_lower, lista_termos):
    """
    Verifica se qualquer termo clínico relevante está presente no texto.

    Parâmetros:
    - texto_lower (str): Texto clínico já normalizado (lowercase)
    - lista_termos (list[str]): Lista de termos associados a um critério clínico

    Retorno:
    - int: 1 se algum termo for encontrado, caso contrário 0

    Observação:
    Esta função é propositalmente simples.
    Toda inteligência clínica deve estar nas funções agregadoras.
    """
    if not texto_lower:
        return 0

    return 1 if any(termo in texto_lower for termo in lista_termos) else 0


# ==============================================================================
# VOCABULÁRIO OFICIAL — CRITÉRIOS DE EXCLUSÃO
# Pacientes que NÃO podem acessar o serviço de gastro/hepato
# ==============================================================================

TERMOS_EXCLUSAO = {

    # 1. Instabilidade Hemodinâmica Grave
    # Risco imediato de vida ou necessidade de suporte intensivo
    'instabilidade_grave': [
        'choque', 'instavel', 'instável', 'noradrenalina', 'dva',
        'dobutamina', 'vasopressora', 'sedado', 'coma', 'hipotenso'
    ],

    # 2. Suporte Ventilatório / Insuficiência Respiratória
    # Pacientes que necessitam de suporte respiratório avançado
    'suporte_ventilatorio': [
        'dispneia', 'insuficiencia respiratoria',
        'intubado', 'iot', 'ventilação mecanica', 'vm', 'tot ',
        'traqueostomia', 'macronebulização', 'cateter de o2',
        'mascara de o2', 'saturação < 90', 'sat < 90'
    ],   

    # 3. Nefrologia / Diálise
    # Pacientes com insuficiência renal grave ou em TRS
    'nefrologia_dialise': [
        'dialise', 'diálise', 'hemodialise', 'hemodiálise',
        'hd ', 'rim', 'urêmico', 'uremico', 'anúrico',
        'terapia renal substitutiva', 'trs', 'creatinina'
    ],

    # 4. Hemorragia Digestiva Ativa
    # Situações de urgência/emergência
    'hemorragia_urgencia': [
        'hda', 'hematemese', 'melena', 'enterorragia',
        'eda de urgencia', 'eda urgencia', 'sangramento ativo',
        'hemorragia digestiva', 'choque hemorragico'
    ],

    # 5. Oncologia Definida Fora do Perfil
    # Pacientes já vinculados à oncologia ou em cuidados paliativos
    'oncologia_definida': [
        'neoplasia', 'neoplasia confirmada', 'acompanhamento oncologico',
        'oncologia clinica', 'quimioterapia', 'radioterapia',
        'tratamento paliativo', 'metastase', 'terminal',
        'fora de possibilidade terapeutica',  
    ],

    # 6. Doenças Infectocontagiosas (Isolamento)
    # Condições que exigem isolamento e inviabilizam acesso
    'doencas_infectocontagiosas': [
        'covid', 'sars-cov', 'tuberculose', 'bk positivo',
        'isolamento aereo', 'isolamento respiratorio'
    ]
}


# ==============================================================================
# VOCABULÁRIO OFICIAL — CRITÉRIOS DE INCLUSÃO (PERFIL GASTRO)
# ==============================================================================

TERMOS_INCLUSAO = {

    # Hepatopatias crônicas ou descompensadas
    'hepatopatia_descompensada': [
        'ascite', 'ictericia', 'ictérica', 'icterica', 'cirrose',
        'cirrose descompensada', 'hepatopatia', 'dhc',
        'encefalopatia', 'biliar', 'colestase',
        'hepatopatia descompensada', 'falencia hepatica'
    ],

    # Doenças Inflamatórias Intestinais
    'doencas_inflamatorias': [
        'diarreia cronica', 'diarreia crônica',
        'diarreia persistente', 'diarreia descompensada',
        'diarreia complicada', 'internamento por diarreia',
        'doença de crohn', 'crohn',
        'retocolite', 'retocolite ulcerativa', 'rcu',
        'dii', 'doenca inflamatoria intestinal',
        'inflamatoria intestinal',
        'refrataria', 'refratária', 'descompensada'
    ],

    # Investigação de Neoplasias Digestivas
    'investigacao_neoplasia': [
        'investigacao de neoplasia', 'investigacao de tumor',
        'tumor abdominal', 'massa abdominal',
        'neoplasia a esclarecer',
        'tumores gastrointestinais',
        'investigacao de tumores gastrointestinais',
        'lesão hepatica', 'lesao hepatica',
        'nodulo hepatico', 'nódulo hepático',
        'nodulo hepatico suspeito',
        'neoplasia hepatica', 'neoplasia hepática',
        'carcinoma a esclarecer',
        'tumor gastrico', 'tumor gástrico',
        'tumor de colon', 'tumor de cólon'
    ],

    # Hepatites Agudas ou Ativas
    'hepatites_agudas': [
        'hepatite aguda',
        'hepatite b', 'hepatite b aguda',
        'hepatite c', 'hepatite c aguda',
        'vhb', 'vhc',
        'hepatite alcoolica', 'hepatite alcoólica aguda',
        'etilismo', 'libação',
        'hepatite autoimune', 'hepatite autoimune aguda', 'hai'
    ],

    # Doenças Colestáticas
    'colestase': [
        'colestase', 'colestatica', 'colestática',
        'doenca hepatica colestatica',
        'doenca hepatica colestatica cronica',
        'colangite biliar primaria', 'cbp',
        'colangite esclerosante primaria', 'cep',
        'colangite esclerosante',
        'prurido', 'coluria'
    ],

    # Doenças Vasculares Hepáticas
    'vascular_hepatico': [
        'budd-chiari', 'sindrome de budd-chiari',
        'doenca hepatica vascular',
        'trombose de veia porta',
        'trombose porto-mesenterica',
        'trombose portomesenterica',
        'trombose mesenterica',
        'trombose porto'
    ],

    # Distúrbios de Deglutição e Nutrição
    'disfagia_nutricao': [
        'disfagia', 'disfagia grave',
        'perda ponderal', 'perda ponderal importante',
        'emagrecimento importante',
        'desnutricao', 'desnutrição'
    ]
}



# ==============================================================================
# FUNÇÕES DE DECISÃO CLÍNICA (AGREGAÇÃO)
# ==============================================================================

def avaliar_exclusao(flags_exclusao):
    """
    Avalia se o paciente possui QUALQUER critério de exclusão.

    Parâmetros:
    - flags_exclusao (dict): flags binárias de exclusão

    Retorno:
    - int: 1 se paciente deve ser excluído, senão 0
    """
    return 1 if any(flags_exclusao.values()) else 0


def avaliar_perfil_gastro(flags_inclusao):
    """
    Avalia se o paciente apresenta perfil compatível com gastro/hepatologia.

    Parâmetros:
    - flags_inclusao (dict): flags binárias de critérios gastro

    Retorno:
    - int: 1 se apresenta perfil gastro, senão 0
    """
    return 1 if any(flags_inclusao.values()) else 0


def avaliar_elegibilidade(flags_exclusao, flags_inclusao):
    """
    Avaliação clínica final de elegibilidade.

    Regras:
    - Se houver qualquer critério de exclusão → NÃO elegível
    - Se houver pelo menos um critério de inclusão → Elegível
    - Caso contrário → Não elegível

    Retorno:
    - int: 1 se elegível, 0 se não elegível
    """
    if avaliar_exclusao(flags_exclusao):
        return 0

    if avaliar_perfil_gastro(flags_inclusao):
        return 1

    return 0


#Recusa:
#creatinina > 3
#clearence creatinina > 15 || creatinina > 3. valor_basal
