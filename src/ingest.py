import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"A variável {name} deve ser definida no arquivo .env.")
    return value


def ingest_pdf() -> None:
    pdf_path = Path(required_env("PDF_PATH"))
    if not pdf_path.is_absolute():
        pdf_path = PROJECT_ROOT / pdf_path
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

    api_key = required_env("OPENAI_API_KEY")
    embedding_model = required_env("OPENAI_EMBEDDING_MODEL")
    database_url = required_env("DATABASE_URL")
    collection_name = required_env("PG_VECTOR_COLLECTION_NAME")

    pages = PyPDFLoader(str(pdf_path)).load()
    if not any(page.page_content.strip() for page in pages):
        raise ValueError(f"Nenhum texto foi extraído do PDF: {pdf_path}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
    )
    chunks = [
        chunk
        for chunk in splitter.split_documents(pages)
        if chunk.page_content.strip()
    ]
    if not chunks:
        raise ValueError(f"Nenhum trecho de texto foi criado a partir de {pdf_path}.")

    embeddings = OpenAIEmbeddings(model=embedding_model, api_key=api_key)
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=database_url,
        use_jsonb=True,
    )
    document_ids = [
        hashlib.sha256(
            f"{pdf_path.resolve()}:{index}:{chunk.page_content}".encode("utf-8")
        ).hexdigest()
        for index, chunk in enumerate(chunks)
    ]
    vector_store.add_documents(documents=chunks, ids=document_ids)
    print(f"Ingestão concluída: {len(chunks)} chunks armazenados em '{collection_name}'.")


if __name__ == "__main__":
    ingest_pdf()
