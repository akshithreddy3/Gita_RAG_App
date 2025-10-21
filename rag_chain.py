# rag_chain.py
import os
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from prompts import SYSTEM_PROMPT, ANSWER_PROMPT

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
TOP_K = int(os.getenv("TOP_K", 4))
MMR = os.getenv("MMR", "true").lower() == "true"
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", 0.0))


def get_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(
        collection_name="gita",
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )


def get_retriever(vs):
    retriever = vs.as_retriever(
        search_type="mmr" if MMR else "similarity",
        search_kwargs={
            "k": TOP_K,
            "score_threshold": SCORE_THRESHOLD,
        },
    )
    return retriever


def format_docs(docs):
    joined = []
    for d in docs:
        src = d.metadata.get("source", "")
        page = d.metadata.get("page_num")
        header = f"[{src} – p.{page}]" if page else f"[{src}]"
        joined.append(f"{header}\n{d.page_content}")
    return "\n\n".join(joined)


def build_chain():
    vectorstore = get_vectorstore()
    retriever = get_retriever(vectorstore)

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=0.2,
        num_ctx=4096,        # reduce if low memory; try 2048
        streaming=False,     # avoid streaming generator disconnects
        keep_alive="30m",    # keep the model loaded
        request_timeout=600,  # tolerate slow first token
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", ANSWER_PROMPT),
    ])

    setup = RunnableParallel({
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    })

    chain = setup | prompt | llm | StrOutputParser()
    return chain, retriever


if __name__ == "__main__":
    chain, retriever = build_chain()
    print("✅ RAG chain built successfully.")
