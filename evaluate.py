
"""
evaluate.py
Script for running automated and manual evaluation of the RAG pipeline using evaluation data.
"""

# --- Imports ---
import pandas as pd
from rag_pipeline import RAGPipeline
import os
import time
from config import *
from langchain_huggingface import HuggingFaceEmbeddings  # For compatibility with new LangChain versions


# --- Evaluation Data Loader ---
def load_evaluation_data(file_path):
    """
    Loads evaluation questions from a CSV file.
    Args:
        file_path (str): Path to the evaluation CSV file.
    Returns:
        pd.DataFrame: DataFrame containing evaluation questions.
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Evaluation data file not found at: {file_path}")
    return pd.read_csv(file_path)


# --- Evaluation Runner ---
def run_evaluation(rag_pipeline: RAGPipeline, eval_df: pd.DataFrame):
    """
    Runs the RAG pipeline against the evaluation questions and collects results.
    Args:
        rag_pipeline (RAGPipeline): The RAG pipeline instance.
        eval_df (pd.DataFrame): DataFrame of evaluation questions.
    Returns:
        pd.DataFrame: DataFrame of evaluation results.
    """
    results = []
    total_questions = len(eval_df)
    print(f"\n--- Starting Evaluation for {total_questions} Questions ---")

    for idx, (_, row) in enumerate(eval_df.iterrows()):
        question = row["question"]
        expected_snippet = row["expected_answer_snippet"]
        is_in_kb = row["is_in_kb"]

        print(f"\n[{idx + 1}/{total_questions}] Question: {question}")
        if pd.isna(expected_snippet) or expected_snippet == '' or expected_snippet == 'N/A':
            print(f"  (Expected KB: {is_in_kb})")
        else:
            print(f"  (Expected KB: {is_in_kb}, Snippet: {str(expected_snippet)[:50]}...)")

        start_time = time.time()
        try:
            assistant_answer, sources = rag_pipeline.query(question)
            end_time = time.time()
            response_time = round(end_time - start_time, 2)
        except Exception as e:
            assistant_answer = f"ERROR: {e}"
            sources = []
            response_time = -1 # Indicate error
            print(f"  Error during query: {e}")

        result = {
            "question": question,
            "expected_answer_snippet": expected_snippet,
            "is_in_kb": is_in_kb,
            "assistant_answer": assistant_answer,
            "retrieved_source_filenames": [os.path.basename(s.metadata.get('source', 'N/A')) for s in sources],
            "retrieved_chunk_contents_preview": [s.page_content[:200] for s in sources],
            "response_time_sec": response_time,
            # --- Manual Assessment Columns (to be filled by you) ---
            "manual_retrieval_relevance": "", # Good/Partial/Bad
            "manual_answer_accuracy": "", # Correct/Partially Correct/Incorrect
            "manual_grounding_faithfulness": "", # Grounded/Hallucinated/Correctly No-Info
            "manual_overall_pass": "" # Yes/No
        }
        results.append(result)
        print(f"  Assistant Answer: {assistant_answer[:100]}...")
        print(f"  Response Time: {response_time}s")

    return pd.DataFrame(results)


# --- Main Evaluation Pipeline ---
def main():
    """
    Main function to run the evaluation pipeline.
    """
    print("Initializing RAG Pipeline for evaluation...")
    try:
        rag_pipeline = RAGPipeline()
    except Exception as e:
        print(f"Failed to initialize RAG Pipeline: {e}")
        print("Please ensure your FAISS index exists (run ingest_data.py) and Ollama server is running with the model pulled.")
        return

    eval_df = load_evaluation_data(EVALUATION_DATA_PATH)
    results_df = run_evaluation(rag_pipeline, eval_df)

    # Save the raw results for manual annotation
    os.makedirs(os.path.dirname(EVALUATION_RESULTS_PATH), exist_ok=True)
    results_df.to_csv(EVALUATION_RESULTS_PATH, index=False)
    print(f"\nRaw evaluation results saved to: {EVALUATION_RESULTS_PATH}")
    print("\n--- Manual Assessment Required ---")
    print("Please open the CSV file and fill in the 'manual_...' columns.")
    print("This qualitative review is critical for understanding your system's performance.")
    print("Once done, summarize your findings in EVALUATION.md.")


if __name__ == "__main__":
    main()