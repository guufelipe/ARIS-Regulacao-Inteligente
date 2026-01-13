
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk  
from nltk.corpus import stopwords
import re

# Baixar stopwords em português se ainda não tiver
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def clean_text_for_nlp(text):
    """
    Limpeza final específica para NLP:
    - Remove pontuação e caracteres especiais
    - Remove números soltos
    - Deixa tudo minúsculo
    """
    if not isinstance(text, str):
        return ""
    
    # Remove caracteres especiais e números, mantém apenas letras e acentos
    text = re.sub(r'[^a-zA-ZáàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]', '', text)
    # Remove espaços extras
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

def vectorize_text(df, text_column='Diagnostico_Texto_Livre', max_features=100):
    """
    Transforma a coluna de texto em uma matriz numérica usando TF-IDF.
    
    Args:
        df: DataFrame contendo a coluna de texto.
        text_column: Nome da coluna de texto.
        max_features: Número máximo de palavras no vocabulário.
    
    Returns:
        df_final: DataFrame original + colunas do TF-IDF
        vectorizer: O objeto treinado (para usar depois em novos dados)
    """
    print("--- Iniciando Vetorização (TF-IDF) ---")
    
    # 1. Limpeza Prévia
    clean_texts = df[text_column].apply(clean_text_for_nlp)
    
    # 2. Configurar Stopwords (palavras para ignorar: "de", "para", "o", "a")
    try:
        pt_stopwords = stopwords.words('portuguese')
    except:
        nltk.download('stopwords')
        pt_stopwords = stopwords.words('portuguese')

    # Adicionar stopwords clínicas comuns que não ajudam na decisão
    custom_stopwords = pt_stopwords + [
        'paciente', 'anos', 'solicito', 'avaliação', 'encaminho', 
        'hospital', 'serviço', 'admissão', 'data', 'hora', 'hd', 'dia'
    ]

    # 3. Configurar TF-IDF
    tfidf = TfidfVectorizer(
        max_features=max_features,
        stop_words=custom_stopwords,
        ngram_range=(1, 2) # Pega palavras sozinhas e pares (ex: "insuficiencia renal")
    )

    # 4. Aprender e Transformar
    try:
        tfidf_matrix = tfidf.fit_transform(clean_texts)
    except ValueError as e:
        print("⚠️ Aviso: O texto está vazio ou só tem stopwords. Retornando DataFrame sem NLP.")
        return df, None
    
    # Criar DataFrame com as palavras
    feature_names = tfidf.get_feature_names_out()
    df_tfidf = pd.DataFrame(
        tfidf_matrix.toarray(), 
        columns=[f"tfidf_{word}" for word in feature_names]
    )
    
    print(f"✅ Vocabulário aprendido: {len(feature_names)} termos.")
    
    # Juntar com o DataFrame original (reset_index é vital para alinhar as linhas)
    df_final = pd.concat([df.reset_index(drop=True), df_tfidf], axis=1)
    
    return df_final, tfidf