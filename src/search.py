import os
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

FALLBACK_ANSWER = "Não tenho informações necessárias para responder sua pergunta."

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "{fallback}"
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "{fallback}"

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "{fallback}"

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "{fallback}"

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"A variável {name} deve ser definida no arquivo .env.")
    return value


def search_prompt() -> Callable[[str], str]:
    api_key = required_env("OPENAI_API_KEY")
    embedding_model = required_env("OPENAI_EMBEDDING_MODEL")
    chat_model = required_env("OPENAI_CHAT_MODEL")
    database_url = required_env("DATABASE_URL")
    collection_name = required_env("PG_VECTOR_COLLECTION_NAME")

    embeddings = OpenAIEmbeddings(model=embedding_model, api_key=api_key)
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=database_url,
        use_jsonb=True,
    )
    llm = ChatOpenAI(model=chat_model, api_key=api_key, temperature=0)

    def answer_question(question: str) -> str:
        if not question.strip():
            raise ValueError("A pergunta não pode estar vazia.")

        results = vector_store.similarity_search_with_score(question, k=10)
        if not results:
            raise RuntimeError(
                "Nenhum documento indexado foi encontrado. Execute src/ingest.py primeiro."
            )

        context = "\n\n".join(document.page_content for document, _ in results)
        prompt = PROMPT_TEMPLATE.format(
            contexto=context,
            pergunta=question,
            fallback=FALLBACK_ANSWER,
        )
        response = llm.invoke(prompt)
        if not isinstance(response.content, str):
            raise TypeError("A resposta do modelo não está em formato de texto.")
        return response.content.strip()

    return answer_question
