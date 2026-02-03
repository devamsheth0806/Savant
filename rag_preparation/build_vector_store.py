import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle

def build_and_save_index():
    import os
    index_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "savant_vector.index")
    metadata_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "savant_metadata.pkl")
    protocols_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "savant_protocols.json")

    # 1. Load the structured protocols we just scraped
    with open(protocols_file, "r") as f:
        data = json.load(f)

    # 2. Prepare Data for Embedding
    documents = []
    metadata = [] 
    
    for protocol in data['protocols']:
        # We embed the keywords and the name to match user voice intent
        text_to_embed = f"{protocol['name']} {', '.join(protocol['keywords'])}"
        documents.append(text_to_embed)
        metadata.append(protocol) # Store full protocol to retrieve later

    # 3. Generate Embeddings (Local Model - Fast & Free)
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2') 
    embeddings = model.encode(documents)

    # 4. Create FAISS Index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))

    # 5. SAVE to Disk (The Hand-off)
    faiss.write_index(index, index_file)
    with open(metadata_file, "wb") as f:
        pickle.dump(metadata, f)
    
    print("Vector Store Built & Saved: savant_vector.index")

if __name__ == "__main__":
    build_and_save_index()