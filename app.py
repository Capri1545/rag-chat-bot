



# --- Imports ---
import gradio as gr
from rag_pipeline import RAGPipeline
import os
from config import *  # Import all config variables for future use

# --- Initialize RAG Pipeline ---
rag_pipeline = RAGPipeline()


# --- Gradio Callback: Get AI Response ---
def get_ai_response(user_query):
    """
    Handles user queries, returns assistant's answer and sources.
    """
    if not user_query.strip():
        return ("<i>Please enter a question.</i>", "")
    try:
        answer, sources = rag_pipeline.query(user_query)
        sources_text = ""
        if sources:
            sources_text = "**Sources Used:**\n\n"
            for i, doc in enumerate(sources):
                source_file_name = os.path.basename(doc.metadata.get('source', 'N/A'))
                sources_text += (
                    f"> **Source {i+1}:** `{source_file_name}` (Chunk ID: `{doc.metadata.get('chunk_id', 'N/A')}`)\n"
                    f"> ```\n{doc.page_content[:300]}...\n```\n\n"
                )
        else:
            sources_text = "_No specific sources were found in the knowledge base to answer this question, or the answer was a canned response._"
        return answer, sources_text
    except Exception as e:
        return (
            f"<span style='color:red'><b>An error occurred during query:</b> {e}<br>"
            "Please ensure your backend and model are available.</span>", "")


# --- Gradio Callback: Clear Fields ---
def clear_fields():
    """
    Clears the input, answer, and sources fields in the UI.
    """
    return "", "", ""


# --- Gradio UI Layout ---
with gr.Blocks(title="Intelligent Knowledge Base Assistant", theme="soft") as demo:
    gr.Markdown(
        """
        # 🧠 Intelligent Knowledge Base Assistant
        <span style='font-size:1.1em'>Ask questions about the Solar System! This assistant retrieves information from a curated knowledge base and uses a Large Language Model to provide accurate, grounded answers.</span>
        """,
        elem_id="header"
    )
    with gr.Row():
        with gr.Column(scale=4):
            query_input = gr.Textbox(
                lines=2,
                placeholder="e.g., What is the diameter of the Sun?",
                label="Your Question:",
                autofocus=True
            )
        with gr.Column(scale=1, min_width=100):
            submit_btn = gr.Button("Get Answer", variant="primary", scale=0)
            clear_btn = gr.Button("Clear", scale=0)
    answer_output = gr.Markdown(label="Assistant's Answer:")
    sources_output = gr.Markdown(label="Sources Used:")
    clear_btn.click(
        fn=clear_fields,
        inputs=[],
        outputs=[query_input, answer_output, sources_output],
        queue=False
    )
    submit_btn.click(
        fn=get_ai_response,
        inputs=query_input,
        outputs=[answer_output, sources_output],
        api_name="ask_question"
    )
    query_input.submit(
        fn=get_ai_response,
        inputs=query_input,
        outputs=[answer_output, sources_output]
    )
    gr.Markdown("---")
    gr.Markdown(
        "<div style='text-align:center; font-size:0.95em;'>Built as a portfolio project for AI Engineering. | <a href='https://github.com/yourusername/rag-chat-bot' target='_blank'>GitHub Repo</a></div>",
        elem_id="footer"
    )

# --- Launch Gradio App ---
demo.launch(show_error=True, share=False)