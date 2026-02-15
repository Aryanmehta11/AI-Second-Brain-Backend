from pypdf import PdfReader

def extract_text_from_pdf(path:str)->str:
    reader=PdfReader(path)
    text=""
    for page in reader.pages:
        text+=page.extract_text() or ""
    return text
