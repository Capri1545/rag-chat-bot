# intelligent-kb-assistant/config.py

import os

# --- Directory Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Get the directory of the current script (config.py)
DATA_DIR = os.path.join(BASE_DIR, "data")
KB_DIRECTORY = os.path.join(DATA_DIR, "knowledge_base")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "faiss_index")
EVALUATION_DATA_PATH = os.path.join(DATA_DIR, "evaluation_data.csv")
EVALUATION_RESULTS_PATH = os.path.join(DATA_DIR, "evaluation_results.csv")

# --- Embedding Model Configuration ---
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# --- LLM Configuration (for Gradio/HuggingFace) ---
LLM_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Used in Gradio app (see app.py)
LLM_BASE_URL = None  # Not used for HuggingFacePipeline/Gradio local model

# --- Document Processing Configuration ---
CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 50 # Overlap between chunks to maintain context

# --- Retrieval Threshold Configuration ---
# Max L2 distance allowed for a document to be considered "relevant enough"
# This value needs tuning based on your specific embedding model and data.
# A common range is 0.5 to 0.8 for L2 distance with normalized embeddings.
RELEVANCE_THRESHOLD_L2 = 0.7 # Tuned value from your testing
TOP_K_RETRIEVAL = 3 # Number of top relevant documents to retrieve for consideration

# --- LLM Prompt Template ---
PROMPT_TEMPLATE = """You are a helpful assistant. Your task is to answer the user's question ONLY based on the provided context.
If the context does not contain enough information to answer the question, or if the question is outside the scope of the provided context,
you MUST respond with: "I'm sorry, but I don't have enough information to answer that based on the provided knowledge base."
DO NOT invent information or use your general knowledge. Focus strictly on the provided context.

Context:
{context}

Question: {question}

Answer:"""