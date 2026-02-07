import pandas as pd
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords

# =============================
# SETUP
# =============================
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

TEXT_COLUMNS = [
    'Justificativa_Internacao',
    'Evolucao',
    'Sinais_Vitais_Texto'
]

# =============================
# LIMPEZA BASE
# =============================
def basic_text_clean(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\sáàâãéèêíïóôõöúçñ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# =============================
# EXTRAÇÃO SEMÂNTICA DE NÚMEROS
# =============================
def extract_clinical_numeric_tokens(text):
    tokens = []

    # Saturação
    match_sat = re.findall(r'sat[o0]2\s*(\d{2})', text)
    for v in match_sat:
        v = int(v)
        if v < 90:
            tokens.append('sato2_baixa')
        elif v < 95:
            tokens.append('sato2_limite')

    # Frequência cardíaca
    match_fc = re.findall(r'fc\s*(\d{2,3})', text)
    for v in match_fc:
        v = int(v)
        if v >= 120:
            tokens.append('taquicardia')
        elif v <= 50:
            tokens.append('bradicardia')

    # Pressão arterial
    match_pa = re.findall(r'pa\s*(\d{2,3})\s*[x/]\s*(\d{2,3})', text)
    for sist, diast in match_pa:
        sist, diast = int(sist), int(diast)
        if sist < 90 or diast < 60:
            tokens.append('hipotensao')

    # Creatinina
    match_creat = re.findall(r'creatinina\s*(\d+[.,]?\d*)', text)
    for v in match_creat:
        v = float(v.replace(',', '.'))
        if v >= 2.0:
            tokens.append('creatinina_alta')

    return tokens

# =============================
# PREPARAÇÃO FINAL PARA NLP
# =============================
def prepare_text_for_vectorization(row):
    textos = []

    for col in TEXT_COLUMNS:
        raw = row.get(col, "")
        cleaned = basic_text_clean(raw)
        numeric_tokens = extract_clinical_numeric_tokens(cleaned)

        bloco = f"{col.lower()} {cleaned} {' '.join(numeric_tokens)}"
        textos.append(bloco)

    return " ".join(textos)

# =============================
# VETORIZAÇÃO TF-IDF
# =============================
def vectorize_text(
    df,
    max_features=300
):
    print("🧠 Iniciando Vetorização TF-IDF (v2 clínica)...")

    # Texto final agregado
    corpus = df.apply(prepare_text_for_vectorization, axis=1)

    # Stopwords
    pt_stopwords = stopwords.words('portuguese')
    custom_stopwords = pt_stopwords + [
        'paciente', 'relata', 'apresenta', 'encontra', 'se',
        'avaliação', 'solicito', 'encaminho', 'hospital',
        'serviço', 'data', 'hora', 'dia', 'quadro', 
    ]

    tfidf = TfidfVectorizer(
        max_features=max_features,
        stop_words=custom_stopwords,
        ngram_range=(1, 3),
        min_df=2
    )

    try:
        tfidf_matrix = tfidf.fit_transform(corpus)
    except ValueError:
        print("⚠️ Texto insuficiente para TF-IDF.")
        return df, None

    feature_names = tfidf.get_feature_names_out()
    df_tfidf = pd.DataFrame(
        tfidf_matrix.toarray(),
        columns=[f"tfidf_{f}" for f in feature_names]
    )

    print(f"✅ Vocabulário clínico aprendido: {len(feature_names)} termos.")

    df_final = pd.concat(
        [df.reset_index(drop=True), df_tfidf],
        axis=1
    )

    return df_final, tfidf
