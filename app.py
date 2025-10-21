# app.py
import os
from dotenv import load_dotenv
import streamlit as st

from rag_chain import build_chain

load_dotenv()

st.set_page_config(page_title="Gita RAG", page_icon="📜", layout="wide")

st.title("📜 Bhagavad Gita – RAG Tutor")
st.caption("Ask questions. Answers come only from your local Bhagavad Gita PDF.")

# Sidebar controls (MUST be indented under the 'with' block)
with st.sidebar:
    st.header("Settings")
    st.write("Model & retrieval settings are in your .env")
    if st.button("↻ Rebuild Vector DB (run ingest)"):
        st.session_state["rebuild"] = True
        st.warning("Open a terminal and run:  `python ingest.py`  then refresh.")

# Build the chain once and keep in session state
if "chain" not in st.session_state or "retriever" not in st.session_state:
    chain, retriever = build_chain()
    st.session_state["chain"] = chain
    st.session_state["retriever"] = retriever

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Render chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
question = st.chat_input("Ask about duty, detachment, karma, devotion…")

if question:
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking from the Gita…"):
            answer = st.session_state["chain"].invoke(question)
            st.markdown(answer)

            # Show sources by re-running retriever for transparency
            with st.expander("Show sources (top-k passages)"):
                docs = st.session_state["retriever"].invoke(question)
                for i, d in enumerate(docs, 1):
                    src = d.metadata.get("source", "")
                    page = d.metadata.get("page_num", "?")
                    st.markdown(f"**{i}. {src} – p.{page}**")
                    st.write(d.page_content)

    st.session_state["messages"].append(
        {"role": "assistant", "content": answer})
