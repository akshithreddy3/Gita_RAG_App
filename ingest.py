import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Load .env
load_dotenv()

# Config
DOCS_DIR = Path(os.getenv("DOCS_DIR", "./data"))
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))
RESET_DB = os.getenv("RESET_DB", "false").lower() == "true"


def load_pdfs(docs_dir: Path):
    pdf_paths = [p for p in docs_dir.glob("**/*.pdf")]
    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found in {docs_dir.resolve()}")

    docs = []
    for pdf_path in pdf_paths:
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        for p in pages:
            p.metadata["source"] = pdf_path.name
            # PyPDFLoader provides 0-based page index in metadata["page"]
            p.metadata["page_num"] = int(p.metadata.get("page", -1)) + 1
        docs.extend(pages)
    return docs


def split_docs(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(docs)


def build_chroma(chunks):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # Optional reset (clean rebuild)
    if RESET_DB:
        import shutil
        if os.path.exists(CHROMA_DIR):
            print("🧹 Resetting Chroma directory...")
            shutil.rmtree(CHROMA_DIR)

    # Create (or re-create) persistent vector store
    db = Chroma(
        collection_name="gita",
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )

    ids = [f"gita-{i}" for i, _ in enumerate(chunks)]
    db.add_documents(chunks, ids=ids)

    print(f"✅ Chroma persisted at {CHROMA_DIR}")
    return db


if __name__ == "__main__":
    print("Loading PDFs…")
    docs = load_pdfs(DOCS_DIR)
    print(f"Loaded {len(docs)} pages")

    print("Splitting…")
    chunks = split_docs(docs)
    print(f"Created {len(chunks)} chunks")

    print("Building Chroma (this may take a few minutes)…")
    db = build_chroma(chunks)
    print("✅ Done. Chroma DB is ready at:", CHROMA_DIR)
