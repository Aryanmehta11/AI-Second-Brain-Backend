from pypdf import PdfReader

def extract_text(path:str)->str:
    reader=PdfReader(path)
    text=""
    for page in reader.pages:
        text+=page.extract_text() or ""
    return text
