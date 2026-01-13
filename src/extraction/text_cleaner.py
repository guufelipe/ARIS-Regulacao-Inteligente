def clean_bad_encoding(text):
    """
    Mapa de correção Versão 7.0 - Ajuste Final (EES = 38 anos).
    Correção chave:
    - ɯ = 8 (Confirmado por EES: ɪɯ -> 38)
    """
    if not text:
        return ""

    replacements = {
        # --- Números Decodificados ---
        'ɵ': '0', 'ɥ': '0',
        'ɨ': '1',           # Confirmado (91 e 71 anos)
        'ɩ': '2',
        'ɪ': '3',           # Confirmado (36 e 38 anos)
        'ɫ': '4',
        'ɬ': '5',
        'ɭ': '6',           # Confirmado (46 anos)
        'c': '6',
        'ɮ': '7',
        'ɯ': '8',           # <--- CORRIGIDO: Era 1, agora confirmado 8
        'ȣ': '8',           # Manter caso apareça outra variante
        'ɰ': '9',           # Confirmado (91 anos)
        
        # --- Símbolos e Pontuação ---
        'ś': ':',
        'ŵ': '/',
        'ſ': '(',
        'ƀ': ')',
        '¿': 'e',
        'Ť': 'e',
        'ɤ': '#',
        'Ş': '-',
        'ţ': ',',
        'Ƌ': '',
        
        # --- Correções de Texto ---
        'anoſs': 'anos',
        'm¿sſes': 'meses',
        'mŤsſes': 'meses'
    }
    
    clean_text = text
    for bad_char, good_char in replacements.items():
        clean_text = clean_text.replace(bad_char, good_char)
        
    return clean_text