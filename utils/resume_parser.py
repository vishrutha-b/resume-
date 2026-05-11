import docx
from pdfminer.high_level import extract_text

def extract_text_from_pdf(file_path):
    return extract_text(file_path)

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []

    for para in doc.paragraphs:
        full_text.append(para.text)

    return "\n".join(full_text)