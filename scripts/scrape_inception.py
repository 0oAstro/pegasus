import os
import time
import re
import json
from PyPDF2 import PdfReader, PdfWriter
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def wait_for_files_active(files):
    """Waits for the given files to be active.

    Some files uploaded to the Gemini API need to be processed before they can be
    used as prompt inputs. The status can be seen by querying the file's "state"
    field.

    This implementation uses a simple blocking polling loop. Production code
    should probably employ a more sophisticated approach.
    """
    print("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    print("...all files ready")
    print()

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
)

def split_and_upload_pdf(file_path):
    pdf = PdfReader(open(file_path, "rb"))
    files = []
    for page_num in range(len(pdf.pages)):
        output_path = f"page_{page_num + 1}.pdf"
        with open(output_path, "wb") as output_file:
            pdf_writer = PdfWriter()
            pdf_writer.add_page(pdf.pages[page_num])
            pdf_writer.write(output_file)
        files.append(upload_to_gemini(output_path, mime_type="application/pdf"))
    return files

def clean_text(text):
    """Cleans the input text by removing unwanted characters and extra spaces."""
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = text.strip()  # Remove leading and trailing spaces
    return text

def sliding_window(text, window_size, step_size):
    """Generates chunks of text using a sliding window approach."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=window_size,
        chunk_overlap=window_size - step_size
    )
    return text_splitter.split_text(text)

# Split the PDF and upload each page
files = split_and_upload_pdf("Inception.pdf")

# Some files have a processing delay. Wait for them to be ready.
wait_for_files_active(files)

# Process each page individually
all_chunks = []
for file in files:
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    file,
                    "give me raw text from this pdf file",
                ],
            },
        ]
    )

    response = chat_session.send_message("INSERT_INPUT_HERE")

    # Clean the response text
    cleaned_text = clean_text(response.text)

    # Perform sliding window to create chunks
    window_size = 1000  # Adjust the window size as needed
    step_size = 500     # Adjust the step size as needed
    chunks = sliding_window(cleaned_text, window_size, step_size)

    # Collect all chunks
    all_chunks.extend([{"chunk_id": len(all_chunks) + i + 1, "text": chunk} for i, chunk in enumerate(chunks)])

# Save chunks to JSON file
with open("cleaned_inception.json", "w") as json_file:
    json.dump(all_chunks, json_file, indent=2)
