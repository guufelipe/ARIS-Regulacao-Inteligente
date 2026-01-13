import fitz  # PyMuPDF
import os

def extract_text_from_pdf(pdf_path):
    """
    Lê um arquivo PDF usando PyMuPDF (fitz).
    Resolve problemas de fontes CID (que aparecem como (cid:622)) e extrai o texto visual.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

    full_text = ""
    
    try:
        # Abre o documento
        with fitz.open(pdf_path) as doc:
            for page in doc:
                # O parâmetro "text" com flag de ordenação ajuda a manter o fluxo de leitura
                text = page.get_text("text", sort=True)
                full_text += text + "\n"
                    
        return full_text
    
    except Exception as e:
        print(f"Erro ao ler PDF {pdf_path}: {e}")
        return ""