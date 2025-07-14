
"""
ingest_data.py
Script for loading, chunking, embedding, and indexing documents into FAISS for the RAG pipeline.
"""

# --- Imports ---
import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import for deprecation warning
from langchain_community.vectorstores import FAISS
from config import *


# --- Document Loader Mapping ---
def get_document_loaders():
    """
    Returns a dictionary of document loaders for different file types.
    """
    return {
        ".txt": TextLoader,
        ".md": TextLoader, # MarkdownLoader also an option, but TextLoader is simpler for now
        ".pdf": PyPDFLoader,
        # Add more loaders as needed (e.g., CSVLoader, JSONLoader)
    }


# --- Document Loading ---
def load_documents(directory):
    """
    Loads documents from a specified directory using appropriate loaders.
    Args:
        directory (str): Path to the directory containing documents.
    Returns:
        list: List of loaded documents.
    """
    documents = []
    file_loaders = get_document_loaders()
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in file_loaders:
                print(f"Loading {file_path}...")
                try:
                    loader = file_loaders[file_extension](file_path)
                    documents.extend(loader.load())
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
            else:
                print(f"Skipping unsupported file: {file_path}")
    print(f"Loaded {len(documents)} raw documents.")
    return documents


# --- Document Chunking ---
def split_documents_into_chunks(documents, chunk_size, chunk_overlap):
    """
    Splits documents into smaller, overlapping chunks.
    Args:
        documents (list): List of loaded documents.
        chunk_size (int): Size of each chunk.
        chunk_overlap (int): Overlap between chunks.
    Returns:
        list: List of chunked documents.
    """
    print(f"Splitting documents into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""] # Prioritize splitting by paragraphs, then lines, then words
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")
    # Add metadata to each chunk for better tracking (if not already present from loader)
    for i, chunk in enumerate(chunks):
        if not hasattr(chunk, 'metadata'):
            chunk.metadata = {}
        chunk.metadata['chunk_id'] = i
        # Attempt to get source if not already present (e.g., for TextLoader)
        if 'source' not in chunk.metadata and hasattr(chunk, 'page_content'):
            pass
    return chunks


# --- Embedding Generation ---
def generate_embeddings(chunks, model_name):
    """
    Generates embeddings for text chunks using a Hugging Face Sentence Transformer model.
    Args:
        chunks (list): List of document chunks (not used for embedding here, but for info/logging).
        model_name (str): Name of the embedding model.
    Returns:
        HuggingFaceEmbeddings: The embedding model instance.
    """
    print(f"Loading embedding model: {model_name}...")
    embeddings_model = HuggingFaceEmbeddings(model_name=model_name)
    print("Embedding model loaded.")
    return embeddings_model


# --- FAISS Index Creation and Saving ---
def create_and_save_faiss_index(chunks, embeddings_model, faiss_path):
    """
    Creates a FAISS index from chunks and embeddings, then saves it to disk.
    Args:
        chunks (list): List of document chunks.
        embeddings_model: Embedding model instance.
        faiss_path (str): Path to save the FAISS index.
    Returns:
        FAISS: The FAISS vectorstore instance.
    """
    print("Creating FAISS index...")
    db = FAISS.from_documents(chunks, embeddings_model)
    print(f"FAISS index created with {db.index.ntotal} vectors.")
    print(f"Saving FAISS index to {faiss_path}...")
    db.save_local(faiss_path)
    print("FAISS index saved successfully.")
    return db


# --- FAISS Index Loading ---
def load_faiss_index(faiss_path, embeddings_model):
    """
    Loads an existing FAISS index from disk.
    Args:
        faiss_path (str): Path to the FAISS index file.
        embeddings_model: Embedding model instance.
    Returns:
        FAISS: The loaded FAISS vectorstore instance.
    """
    print(f"Loading FAISS index from {faiss_path}...")
    db = FAISS.load_local(faiss_path, embeddings_model, allow_dangerous_deserialization=True)
    print("FAISS index loaded successfully.")
    return db


# --- Main Ingestion Pipeline ---
def main():
    """
    Main function to run the data ingestion pipeline.
    """
    # Ensure FAISS index directory exists
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)

    # 1. Load documents
    raw_documents = load_documents(KB_DIRECTORY)
    if not raw_documents:
        print("No documents found to process. Please ensure files are in data/knowledge_base/.")
        return

    # 2. Split into chunks
    chunks = split_documents_into_chunks(raw_documents, CHUNK_SIZE, CHUNK_OVERLAP)

    # 3. Generate embeddings model
    embeddings_model = generate_embeddings(chunks, EMBEDDING_MODEL_NAME)

    # 4. Create and save FAISS index
    create_and_save_faiss_index(chunks, embeddings_model, FAISS_INDEX_PATH)

    print("\nData ingestion pipeline completed!")
    print(f"Knowledge base indexed and saved to {FAISS_INDEX_PATH}")

if __name__ == "__main__":
    main()