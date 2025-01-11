import os
from PyPDF2 import PdfReader

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

import nltk
nltk.download("punkt")
nltk.download("punkt_tab")

def split_into_chunks(text, chunk_size=500):
    sentences = nltk.tokenize.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0
    for sentence in sentences:
        if current_length + len(sentence.split()) > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(sentence)
        current_length += len(sentence.split())
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

print(split_into_chunks(extract_text_from_pdf("COS.pdf")))
