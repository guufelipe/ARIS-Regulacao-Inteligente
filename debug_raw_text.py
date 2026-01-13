import fitz # Certifique-se que instalou: pip install pymupdf
import re

def analyze_pdf(path):
    print(f"\n--- ANALISANDO: {path} ---")
    try:
        with fitz.open(path) as doc:
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"
        
        # Limpa espaços excessivos para facilitar a leitura no terminal
        text_oneline = " ".join(text.split())
        
        print(f"[{path}] TAMANHO DO TEXTO: {len(text)} caracteres")
        
        # Snippet para o problema do CML (Idade)
        # Procura onde diz "IDADE" e mostra os 20 caracteres seguintes
        match_idade = re.search(r'IDADE', text_oneline, re.IGNORECASE)
        if match_idade:
            start = match_idade.start()
            print(f"[{path}] TRECHO IDADE RAW: '{text_oneline[start:start+30]}'")
        else:
            print(f"[{path}] 'IDADE' NÃO ENCONTRADO NO TEXTO RAW.")

        # Snippet para o problema do CWSS (Diagnóstico)
        # Mostra o texto ao redor de 'SINAIS E SINTOMAS'
        match_diag = re.search(r'SINAIS E SINTOMAS', text_oneline, re.IGNORECASE)
        if match_diag:
            start = match_diag.start()
            # Mostra 50 chars antes e 200 depois para entendermos o contexto
            print(f"[{path}] TRECHO DIAGNÓSTICO RAW:\n...{text_oneline[start-50:start+250]}...")
        else:
            print(f"[{path}] 'SINAIS E SINTOMAS' NÃO ENCONTRADO. TENTANDO 'QUADRO CLÍNICO'...")
            # Fallback debug
            match_qc = re.search(r'QUADRO CLÍNICO', text_oneline, re.IGNORECASE)
            if match_qc:
                start = match_qc.start()
                print(f"[{path}] TRECHO QUADRO CLÍNICO RAW:\n...{text_oneline[start:start+250]}...")

    except Exception as e:
        print(f"ERRO AO LER {path}: {e}")

if __name__ == "__main__":
    analyze_pdf("data/raw/CML.pdf")
    analyze_pdf("data/raw/CWSS.pdf")