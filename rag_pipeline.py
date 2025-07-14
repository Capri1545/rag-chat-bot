
"""
rag_pipeline.py
Core RAG pipeline class for retrieval, LLM inference, and answer extraction.
"""

# --- Imports ---
import os
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.schema import Document # Import Document for type hinting if needed
from config import *


# --- RAG Pipeline Class ---
class RAGPipeline:
    def __init__(self):
        """
        Initializes the RAGPipeline, loading embeddings, FAISS index, and LLM.
        """
        self.vectorstore = None
        self.embeddings_model = None
        self.llm = None
        self.qa_chain = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """
        Initializes the embedding model, loads FAISS index, and sets up HuggingFace LLM.
        """
        print("Initializing RAG Pipeline components...")
        # 1. Load embedding model
        try:
            self.embeddings_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
            print("Embedding model loaded.")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            raise

        # 2. Load FAISS index
        if not os.path.exists(FAISS_INDEX_PATH):
            raise FileNotFoundError(
                f"FAISS index not found at {FAISS_INDEX_PATH}. "
                "Please run ingest_data.py first to create the index."
            )
        try:
            self.vectorstore = FAISS.load_local(FAISS_INDEX_PATH, self.embeddings_model, allow_dangerous_deserialization=True)
            print("FAISS index loaded successfully.")
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            raise

        # 3. Initialize HuggingFace LLM
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from transformers.pipelines import pipeline
            print(f"Initializing HuggingFacePipeline LLM: {LLM_MODEL_NAME}...")
            tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME)
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                pad_token_id=tokenizer.eos_token_id,
                device=0
            )
            self.llm = HuggingFacePipeline(pipeline=pipe)
            print(f"HuggingFacePipeline LLM '{LLM_MODEL_NAME}' initialized successfully.")
        except Exception as e:
            print(f"Error initializing HuggingFace LLM: {e}")
            print("Please ensure the model is available and your environment has the required dependencies.")
            raise


    def _get_relevant_documents_with_threshold(self, query: str):
        """
        Retrieves only the single most relevant document (k=1) and applies a relevance threshold.
        Returns a list of (Document, score) tuples for relevant documents.
        """
        if self.embeddings_model is None:
            raise RuntimeError("Embeddings model is not initialized.")
        query_embedding = self.embeddings_model.embed_query(query)
        if self.vectorstore is None:
            raise RuntimeError("Vectorstore is not initialized.")
        results = self.vectorstore.similarity_search_by_vector(query_embedding, k=TOP_K_RETRIEVAL)
        filtered_docs_with_scores = []
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                doc, score = result
            else:
                doc, score = result, 0.0
            if isinstance(score, (float, int)) and score <= RELEVANCE_THRESHOLD_L2:
                filtered_docs_with_scores.append((doc, score))
            else:
                src = getattr(doc, 'metadata', {}).get('source', 'N/A')
                print(f"  Debug: Filtering out document due to low relevance score: {score} > {RELEVANCE_THRESHOLD_L2} (Source: {src})")
        return filtered_docs_with_scores


    def query(self, user_query: str):
        """
        Queries the RAG pipeline with a user question, using only the most relevant chunk, minimal prompt, and answer post-processing.
        Returns the LLM's answer and source documents, or fallback if not relevant.
        """
        try:
            if not (self.vectorstore and self.llm):
                return ("RAG Pipeline components not initialized.", [])

            print(f"Processing query: '{user_query}'")

            # Step 1: Retrieve only the single most relevant chunk for context, with score
            retrieved_docs_with_scores = self.vectorstore.similarity_search_with_score(user_query, k=1)
            if not retrieved_docs_with_scores:
                print("No sufficiently relevant documents found. Returning canned response.")
                return ("I'm sorry, but I don't have enough information to answer that based on the provided knowledge base.", [])

            top_doc, top_score = retrieved_docs_with_scores[0]
            print(f"[DEBUG] Top document score for query '{user_query}': {top_score}")
            import numbers
            if not isinstance(top_score, numbers.Number):
                print(f"Top document score is not a number. Returning fallback answer.")
                return ("I'm sorry, but I don't have enough information to answer that based on the provided knowledge base.", [])
            if float(top_score) > RELEVANCE_THRESHOLD_L2:
                print(f"Top document score {top_score} exceeds threshold {RELEVANCE_THRESHOLD_L2}. Returning fallback answer.")
                return ("I'm sorry, but I don't have enough information to answer that based on the provided knowledge base.", [])

            context = getattr(top_doc, "page_content", str(top_doc))
            minimal_prompt = PROMPT_TEMPLATE.format(context=context, question=user_query)

            answer = self.llm.invoke(minimal_prompt)
            # HuggingFacePipeline may return a list of dicts or a string
            if isinstance(answer, list) and len(answer) > 0:
                first = answer[0]
                if isinstance(first, dict) and "generated_text" in first:
                    generated = first.get("generated_text", "")
                    answer_text = generated[len(minimal_prompt):].strip()
                else:
                    answer_text = str(first).strip()
            else:
                answer_text = str(answer).strip()

            for stop in ["\nQuestion:", "\nQ:", "\nUser:"]:
                if stop in answer_text:
                    answer_text = answer_text.split(stop)[0].strip()

            return (answer_text, [top_doc])
        except Exception as e:
            print(f"Error during query: {e}")
            return (f"An error occurred during query: {e}", [])


# --- Debug CLI Entry Point (Optional) ---
# if __name__ == "__main__":
#     try:
#         rag_pipeline = RAGPipeline()
#         print("\n--- Intelligent Knowledge Base Assistant (Debug Mode) ---")
#         print("Type your questions about the Solar System (or 'exit' to quit).")
#
#         while True:
#             user_question = input("Ask a question (or type 'exit'): ").strip()
#             if user_question.lower() == 'exit':
#                 print("Goodbye!")
#                 break
#             if not user_question:
#                 continue
#
#             answer, sources = rag_pipeline.query(user_question)
#             print("\nAssistant Answer:")
#             print(answer)
#             if sources:
#                 print("\nSources Used:")
#                 for i, doc in enumerate(sources):
#                     print(f"  {i+1}. Source: {doc.metadata.get('source', 'N/A')} (Chunk ID: {doc.metadata.get('chunk_id', 'N/A')})")
#             else:
#                 print("No specific sources were used as the answer was a canned response due to insufficient relevance.")
#             print("-" * 50)
#     except Exception as e:
#         print(f"An error occurred during pipeline initialization or query: {e}")