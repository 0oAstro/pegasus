import json
import nltk
from nltk.tokenize import sent_tokenize

# Download the punkt tokenizer models
nltk.download('punkt')
nltk.download('punkt_tab')

# Function to chunk text using NLTK
def chunk_text_with_nltk(text, chunk_size=5):
    sentences = sent_tokenize(text)
    chunks = []
    chunk = []
    for sentence in sentences:
        chunk.append(sentence)
        if len(chunk) >= chunk_size:
            chunks.append(" ".join(chunk))
            chunk = []
    if chunk:
        chunks.append(" ".join(chunk))
    return chunks

# Function to save chunks to JSON
def save_chunks_to_json(chunks, json_path):
    chunk_data = [{"id": i, "text": chunk} for i, chunk in enumerate(chunks)]
    with open(json_path, 'w') as file:
        json.dump(chunk_data, file, indent=4)

# Main function
def main(pdf_path, json_path):
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)

    # Chunk text using NLTK
    chunks = chunk_text_with_nltk(text)

    # Save chunks to JSON
    save_chunks_to_json(chunks, json_path)

# Example usage
pdf_path = 'Inception.pdf'
json_path = 'chunk_inception.json'

main(pdf_path, json_path)
