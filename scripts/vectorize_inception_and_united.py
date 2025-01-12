import os
import json
from tqdm import tqdm
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Load environment variables
QDRANT_URL = os.getenv('QDRANT_ENDPOINT')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

# Initialize Qdrant client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, grpc_port=6333)

# Initialize the embedder
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Create collections
collections = ['united', 'inception']
for collection in collections:
    client.create_collection(
        collection_name=collection,
        vectors_config={
            "size": embedder.get_sentence_embedding_dimension(),
            "distance": "Cosine"
        }
    )

# Function to load data and add to Qdrant
def load_and_add_to_qdrant(file_path, collection_name):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    for item in tqdm(data, desc=f"Processing {collection_name}"):
        text = item['text']
        vector = embedder.encode(text).tolist()
        client.upsert(
            collection_name=collection_name,
            points=[{
                'id': item['chunk_id'],
                'vector': vector,
                'payload': item
            }]
        )

# Load and add data to respective collections
load_and_add_to_qdrant('cleaned_inception.json', 'inception')
load_and_add_to_qdrant('cleaned_united.json', 'united')

print("Data has been successfully added to the collections.")