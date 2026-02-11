import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from nltk.corpus import stopwords
    _NLTK_AVAILABLE = True
except Exception:
    _NLTK_AVAILABLE = False

from src.extraction.text_cleaner import clean_bad_encoding


def basic_text_clean(text: str) -> str:
    """Limpeza básica do texto clínico.

    - Corrige caracteres ruins (mapeamento customizado)
    - Converte para minúsculas
    - Normaliza separadores (x, /) comuns em medidas
    - Remove caracteres não alfanuméricos (mantém acentos)
    - Compacta espaços
    """
    if text is None:
        return ""

    t = str(text)
    t = clean_bad_encoding(t)
    t = t.lower()

    # Normaliza separadores comuns
    t = t.replace("×", "x").replace("/", " x ")

    # Mantém letras com acentos, dígitos e espaços; remove outros símbolos
    t = re.sub(r"[^a-zA-Záàâãéèêíïóôõöúçñ0-9\sx]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_clinical_numeric_tokens(text: str) -> list:
    """Extrai tokens numéricos clínicos relevantes.

    Gera tokens padronizados para valores típicos:
    - PA (pressão arterial): 120x80 -> pa_120_80
    - SatO2: sat o2 96 -> sato2_96
    - Qualquer número isolado: 38 -> num_38
    """
    if not text:
        return []

    tokens = set()

    # PA: 120x80, 120/80
    for m in re.finditer(r"\b(\d{2,3})\s*(?:x|/)\s*(\d{2,3})\b", text):
        sys, dia = m.group(1), m.group(2)
        tokens.add(f"pa_{sys}_{dia}")

    # SatO2: sat o2 96, sato2 96, sat 96
    for m in re.finditer(r"\b(?:sato?2|sat|o2)\D{0,3}(\d{2,3})\b", text):
        val = m.group(1)
        tokens.add(f"sato2_{val}")

    # Genéricos: números com ponto ou vírgula
    for m in re.finditer(r"\b\d+(?:[\.,]\d+)?\b", text):
        val = m.group(0).replace(",", ".")
        # Evita duplicar valores que já foram parte da PA
        if re.fullmatch(r"\d+(?:\.\d+)?", val):
            tokens.add(f"num_{val}")

    return sorted(tokens)


def vectorize_text(
    df,
    text_columns=None,  # parâmetro aceito para compatibilidade
    max_features=300
):
    print("🧠 Iniciando Vetorização TF-IDF (v2 clínica)...")

    # =============================
    # STOPWORDS
    # =============================
    if _NLTK_AVAILABLE:
        try:
            pt_stopwords = stopwords.words("portuguese")
        except Exception:
            # Fallback leve se corpus não estiver disponível
            pt_stopwords = [
                "de", "do", "da", "dos", "das", "e", "a", "o",
                "as", "os", "um", "uma", "por", "com", "sem", "em",
            ]
    else:
        pt_stopwords = [
            "de", "do", "da", "dos", "das", "e", "a", "o",
            "as", "os", "um", "uma", "por", "com", "sem", "em",
        ]

    custom_stopwords = pt_stopwords + [
        "paciente", "relata", "apresenta", "encontra", "se",
        "avaliacao", "avaliação", "solicito", "encaminho", "hospital",
        "servico", "serviço", "data", "hora", "dia", "quadro",
        "dias", "horas", "anos", "ano",
        "mes", "meses", "semana", "semanas",
        "aguardo", "retorno", "exame", "exames",
        "realizado", "realizados",
        "ontem", "hoje", "amanha",
        "aguardando", "realizar",
        "disponibilidade", "regulacao", "regulação",
        "internacao", "internação", "alta",
        "evolucao", "evolução", "sinais", "vitais", "texto",
        "situacao", "situação", "condicao", "condição",
        "diagnostico", "diagnóstico",
        "tratamento", "medicacao", "medicação",
        "retrata","confirmação", "confirmacao", "observacao", "observação", "digitação"
        "alteração", "amanda", "alteracao", "melhora", "piora", "estável", "estavel", "alterada", "alterado","tipo"
        "alteraçao", "alteraçoes"
    ]

    # =============================
    # COLUNAS DE TEXTO (EFETIVAS)
    # =============================
    TEXT_COLUMNS = text_columns or []

    # =============================
    # PREPARAÇÃO FINAL PARA NLP
    # =============================
    def prefix_tokens(text: str, prefix: str) -> str:
        # Removido o prefixo do campo; mantemos apenas os tokens limpos
        return " ".join(text.split())

    def prepare_text_for_vectorization(row: pd.Series) -> str:
        textos = []
        for col in TEXT_COLUMNS:
            raw = row.get(col, "")
            cleaned = basic_text_clean(raw)
            numeric_tokens = extract_clinical_numeric_tokens(cleaned)
            texto_sem_prefixo = prefix_tokens(cleaned, col.lower())
            tokens_sem_prefixo = " ".join(numeric_tokens)
            textos.append(f"{texto_sem_prefixo} {tokens_sem_prefixo}")
        return " ".join(textos).strip()

    # =============================
    # TEXTO FINAL AGREGADO
    # =============================
    corpus = df.apply(prepare_text_for_vectorization, axis=1).tolist()

    # =============================
    # TF-IDF
    # =============================
    tfidf = TfidfVectorizer(
        max_features=max_features,
        stop_words=custom_stopwords,
        ngram_range=(1, 3),
        min_df=3,
        max_df=0.9,
        token_pattern=r"(?u)\b[a-zA-Záàâãéèêíïóôõöúçñ_]{3,}\b",
    )

    try:
        tfidf_matrix = tfidf.fit_transform(corpus)
    except ValueError:
        print("⚠️ Texto insuficiente para TF-IDF.")
        return df, None

    # =============================
    # FEATURES APRENDIDAS (AUDITORIA)
    # =============================
    feature_names = tfidf.get_feature_names_out()
    df_features = pd.DataFrame({"feature": feature_names})

    print("\n📊 Total de features aprendidas:")
    print(len(feature_names))

    # =============================
    # DATAFRAME TF-IDF
    # =============================
    df_tfidf = pd.DataFrame(
        tfidf_matrix.toarray(),
        columns=[f"tfidf_{f}" for f in feature_names],
    )

    print(f"\n✅ Vocabulário clínico aprendido: {len(feature_names)} termos.")

    # =============================
    # CONCAT FINAL
    # =============================
    df_final = pd.concat([df.reset_index(drop=True), df_tfidf], axis=1)

    return df_final, tfidf
