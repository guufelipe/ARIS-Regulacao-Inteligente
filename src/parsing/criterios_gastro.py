"""
Módulo de Inteligência Médica do ARIS - GASTRO-HEPATOLOGIA.
Baseado no Protocolo de Acesso Oficial (HC-UFPE).
"""

def verificar_criterio(texto_lower, lista_termos):
    """
    Retorna 1 se qualquer termo da lista estiver no texto, senão 0.
    """
    if not texto_lower:
        return 0
    return 1 if any(termo in texto_lower for termo in lista_termos) else 0

# ==============================================================================
# CRITÉRIOS DE EXCLUSÃO (NÃO PODERÃO TER ACESSO)
# ==============================================================================
TERMOS_EXCLUSAO = {
    # 1. Instabilidade Hemodinâmica
    'instabilidade_grave': [
        'choque', 'instavel', 'instável', 'noradrenalina', 'dva', 
        'dobutamina', 'vasopressora', 'sedado', 'coma', 'hipotenso'
    ],

    # 2. Suporte Ventilatório
    'suporte_ventilatorio': [
        'dispneia', 'desconforto respiratorio', 'insuficiencia respiratoria',
        'intubado', 'iot', 'ventilação mecanica', 'vm', 'tot ', 
        'traqueostomia', 'macronebulização', 'cateter de o2', 
        'mascara de o2', 'saturação < 90', 'sat < 90'
    ],

    # 3. Nefrologia / Diálise
    'nefrologia_dialise': [
        'dialise', 'diálise', 'hemodialise', 'hemodiálise', 
        'hd ', 'rim', 'urêmico', 'uremico', 'anúrico', 
        'terapia renal substitutiva', 'trs'
    ],

    # 4. Hemorragia Ativa
    'hemorragia_urgencia': [
        'hda', 'hematemese', 'melena', 'enterorragia', 
        'eda de urgencia', 'eda urgencia', 'sangramento ativo', 
        'hemorragia digestiva', 'choque hemorragico'
    ],

    # 5. Oncologia Definida
    'oncologia_definida': [
        'neoplasia confirmada', 'acompanhamento oncologico', 'oncologia clinica',
        'quimioterapia', 'radioterapia', 'tratamento paliativo', 
        'metastase', 'terminal', 'fora de possibilidade terapeutica'
    ],

    # 6. Doenças Infectocontagiosas (Isolamento)
    'doencas_infectocontagiosas': [
        'covid', 'sars-cov', 'tuberculose', 'bk positivo', 
        'isolamento aereo', 'isolamento respiratorio'
    ]
}

# ==============================================================================
# CRITÉRIOS DE INCLUSÃO (PERFIL GASTRO)
# ==============================================================================
TERMOS_INCLUSAO = {
    'hepatopatia_descompensada': [
        'ascite', 'ictericia', 'ictérica', 'icterica', 'cirrose', 
        'hepatopatia', 'dhc', 'encefalopatia', 'biliar', 'colestase'
    ],
    'doencas_inflamatorias': [
        'diarreia cronica', 'diarreia persistente', 'doença de crohn', 
        'retocolite', 'rcu', 'dii', 'inflamatoria intestinal', 'refrataria'
    ],
    'investigacao_neoplasia': [
        'tumor abdominal', 'massa abdominal', 'neoplasia a esclarecer', 
        'lesão hepatica', 'lesao hepatica', 'nodulo hepatico', 
        'carcinoma a esclarecer', 'tumor gastrico', 'tumor de colon'
    ],
    'hepatites_agudas': [
        'hepatite b', 'hepatite c', 'vhb', 'vhc', 'hepatite alcoolica', 
        'etilismo', 'libação', 'hepatite autoimune', 'hai'
    ],
    'colestase': [
        'colestase', 'colestatica', 'colangite biliar', 'cbp', 
        'colangite esclerosante', 'cep', 'prurido', 'coluria'
    ],
    'vascular_hepatico': [
        'budd-chiari', 'trombose de veia porta', 'trombose porto', 
        'trombose mesenterica'
    ]
}