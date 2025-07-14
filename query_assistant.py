
"""
query_assistant.py
Helper functions for loading FAISS index, embeddings, and initializing LLMs for the RAG pipeline.
"""

# --- Imports ---
import os
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_community.vectorstores import FAISS
from config import FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME, LLM_MODEL_NAME, PROMPT_TEMPLATE
from typing import Tuple, Any

# --- FAISS Index and Embeddings Loader ---
def load_faiss_index_and_embeddings(faiss_path: str, embedding_model_name: str) -> Tuple[Any, Any]:
    """
    Loads the FAISS index and embedding model.
    Args:
        faiss_path (str): Path to the FAISS index file.
        embedding_model_name (str): Name of the embedding model.
    Returns:
        Tuple[Any, Any]: (FAISS vectorstore, embeddings model)
    Raises:
        FileNotFoundError: If the FAISS index file does not exist.
    """
    if not os.path.exists(faiss_path):
        raise FileNotFoundError(f"FAISS index not found at {faiss_path}. Please run ingest_data.py first.")
    print(f"Loading embedding model: {embedding_model_name}...")
    embeddings_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
    print("Embedding model loaded.")
    print(f"Loading FAISS index from {faiss_path}...")
    db = FAISS.load_local(faiss_path, embeddings_model, allow_dangerous_deserialization=True)
    print("FAISS index loaded successfully.")
    return db, embeddings_model

# --- LLM Initialization ---
def initialize_llm(model_name: str) -> HuggingFacePipeline:
    """
    Initializes the HuggingFacePipeline LLM.
    Args:
        model_name (str): Name of the HuggingFace model to load.
    Returns:
        HuggingFacePipeline: The initialized LLM pipeline.
    """
    print(f"Initializing HuggingFacePipeline LLM: {model_name}...")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from transformers.pipelines import pipeline
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            pad_token_id=tokenizer.eos_token_id,
            device=0
        )
        llm = HuggingFacePipeline(pipeline=pipe)
        print(f"HuggingFacePipeline LLM '{model_name}' initialized successfully.")
        return llm
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        raise

# --- CLI Entry Point (Uncomment to enable CLI mode) ---
# def main() -> None:
#     """
#     Main entry point for the CLI assistant.
#     """
#     try:
#         vectorstore, embeddings_model = load_faiss_index_and_embeddings(FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME)
#         llm = initialize_llm(LLM_MODEL_NAME)
#     except Exception as e:
#         print(f"Initialization failed: {e}")
#         return
#
#     print("\n--- Intelligent Knowledge Base Assistant ---")
#     print("Type your questions about the Solar System (or 'exit' to quit).")
#
#     while True:
#         query = input("\nYour question: ").strip()
#         if query.lower() == 'exit':
#             print("Exiting assistant. Goodbye!")
#             break
#         if not query:
#             print("Please enter a question.")
#             continue
#
#         print("Searching for relevant information...")
#         try:
#             # Only use the single most relevant chunk for context
#             retrieved_docs_with_scores = vectorstore.similarity_search_with_score(query, k=1)
#             if not retrieved_docs_with_scores:
#                 print("\nAssistant's Answer:")
#                 print("I'm sorry, but I don't have enough information to answer that based on the provided knowledge base.")
#                 continue
#
#             top_doc = retrieved_docs_with_scores[0][0]
#             context = getattr(top_doc, "page_content", str(top_doc))
#             prompt = PROMPT_TEMPLATE.format(context=context, question=query)
#             print("Generating answer using LLM...")
#             answer = llm.invoke(prompt)
#             if isinstance(answer, list):
#                 first = answer[0]
#                 if isinstance(first, dict) and "generated_text" in first:
#                     generated_text = first.get("generated_text", "")
#                     answer = generated_text[len(prompt):].strip()
#                 else:
#                     answer = str(first)
#             elif hasattr(answer, "__str__"):
#                 answer = str(answer)
#             else:
#                 answer = str(answer)
#
#             # Only show the first answer, stop at next Q or User or similar
#             answer_text = answer.strip()
#             for stop in ["\nQuestion:", "\nQ:", "\nUser:"]:
#                 if stop in answer_text:
#                     answer_text = answer_text.split(stop)[0].strip()
#             print("\nAssistant's Answer:")
#             print(answer_text)
#         except Exception as e:
#             print(f"An error occurred during query: {e}")
#             # Optionally, log the error or provide more guidance
#
# if __name__ == "__main__":
#     main()