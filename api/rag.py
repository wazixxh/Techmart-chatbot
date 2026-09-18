"""RAG pipeline over TechMart's policy document and product catalogue.

Loads policy.txt and products.xlsx, embeds them with Gemini, and exposes a
history-aware retrieval chain. Import `build_rag_chain` from the Streamlit app,
or run this file directly for a quick command-line check.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import os
from dotenv import load_dotenv

def get_api_key() -> str | None:
    return (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
        or os.environ.get("GEMINI_KEY")
        or os.environ.get("GOOGLE_KEY")
    )

load_dotenv()
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
POLICY_PATH = BASE_DIR / "policy.txt"
PRODUCTS_PATH = BASE_DIR / "products.xlsx"
INDEX_DIR = BASE_DIR / "faiss_index"
DEFAULT_K = 5

CHAT_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-2"

# Only used when a single policy chapter is too long to embed whole.
POLICY_CHUNK_SIZE = 600
POLICY_CHUNK_OVERLAP = 80

ANSWER_SYSTEM_PROMPT = """You are TechMart's customer support assistant.

Answer using only the context below, which holds TechMart's customer policies \
and product catalogue. If the context does not contain the answer, say so \
plainly and point the customer to support@techmart.com. Never invent prices, \
stock levels, or timeframes.

Quote exact figures when the context provides them. Keep answers short and
concrete, and mention the product name when you recommend something.

Context:
{context}"""

CONDENSE_SYSTEM_PROMPT = """Given the conversation so far and a follow-up \
message, rewrite the follow-up as a standalone question that makes sense \
without the conversation. Keep the customer's original wording where you can. \
Return only the rewritten question, nothing else."""


def _is_chapter_heading(line: str) -> bool:
    """Chapter headings in policy.txt are short, all-caps, unpunctuated lines."""
    stripped = line.strip()
    return (
        bool(stripped)
        and len(stripped) <= 60
        and any(char.isalpha() for char in stripped)
        and stripped == stripped.upper()
        and not stripped.endswith((".", ":", ","))
    )


def split_policy_chapters(text: str) -> list[tuple[str, str]]:
    """Split the policy text into (heading, body) pairs, one per chapter."""
    chapters: list[tuple[str, str]] = []
    heading = "GENERAL"  # covers any text before the first heading
    body: list[str] = []

    def flush() -> None:
        if any(line.strip() for line in body):
            chapters.append((heading, "\n".join(body).strip()))

    for line in text.splitlines():
        if _is_chapter_heading(line):
            flush()
            heading = line.strip()
            body = []
        else:
            body.append(line)

    flush()
    return chapters


def load_policy_documents(path: Path = POLICY_PATH) -> list[Document]:
    """One document per policy chapter, so a chunk always carries its heading."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=POLICY_CHUNK_SIZE,
        chunk_overlap=POLICY_CHUNK_OVERLAP,
        separators=["\n", ". ", " ", ""],
    )

    documents: list[Document] = []
    for heading, body in split_policy_chapters(path.read_text(encoding="utf-8")):
        # Chapters are short enough to embed whole; this only splits the rare
        # long one, and repeats the heading so each part still stands alone.
        parts = splitter.split_text(body) or [body]
        for index, part in enumerate(parts, start=1):
            documents.append(
                Document(
                    page_content=f"{heading}\n{part}",
                    metadata={
                        "source": path.name,
                        "type": "policy",
                        "chapter": heading,
                        "part": index,
                        "parts": len(parts),
                    },
                )
            )
    return documents


def load_product_documents(path: Path = PRODUCTS_PATH) -> list[Document]:
    """One document per catalogue row, so retrieval returns whole products."""
    df = pd.read_excel(path)
    # The sheet has trailing rows where only Category is filled with a stray
    # number; drop anything without a real product on it.
    df = df.dropna(subset=["Brand", "Model Name", "price"])

    documents: list[Document] = []
    for _, row in df.iterrows():
        stock = int(row["stock"]) if pd.notna(row["stock"]) else 0
        availability = f"{stock} units in stock" if stock else "Out of stock"
        name = f"{row['Brand']} {row['Model Name']}"
        content = "\n".join(
            [
                f"Product: {name}",
                f"Category: {row['Category']}",
                f"Brand: {row['Brand']}",
                f"Key specifications: {row['Key Specifications']}",
                f"Best for: {row['Best For']}",
                f"Price: ${row['price']:.2f}",
                f"Availability: {availability}",
            ]
        )
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": path.name,
                    "type": "product",
                    "product": name,
                    "category": str(row["Category"]),
                    "price": float(row["price"]),
                    "stock": stock,
                },
            )
        )
    return documents


def load_documents() -> list[Document]:
    return load_policy_documents() + load_product_documents()


def missing_sources() -> list[str]:
    return [path.name for path in (POLICY_PATH, PRODUCTS_PATH) if not path.exists()]


def vector_backend() -> str:
    return "FAISS"


def corpus_stats() -> list[dict]:
    policy = load_policy_documents()
    products = load_product_documents()
    return [
        {"label": "Policy", "name": POLICY_PATH.name, "detail": "Company policies", "chunks": len(policy), "items": sorted({d.metadata.get("chapter", "GENERAL") for d in policy})},
        {"label": "Products", "name": PRODUCTS_PATH.name, "detail": "Product catalogue", "chunks": len(products), "items": sorted({d.metadata.get("category", "Other") for d in products})},
    ]


def describe_source(document: Document) -> str:
    metadata = document.metadata
    return metadata.get("product") or metadata.get("chapter") or metadata.get("source", "Source")


def build_vectorstore(*, rebuild: bool = False) -> FAISS:
    """Load the saved FAISS index, or embed the source files and save one."""
    api_key = get_api_key()
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)

    if INDEX_DIR.exists() and not rebuild:
        # Safe here because this index is only ever written by build_vectorstore
        # below; never point this at an index from an untrusted source.
        try:
            store = FAISS.load_local(
                str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
            )
            # Saved indexes can outlive an embedding-model change. FAISS only
            # reports the mismatch later as the opaque assertion ``d == self.d``.
            query_dimensions = len(
                embeddings.embed_query("index compatibility check")
            )
            if store.index.d == query_dimensions:
                return store
        except (AssertionError, ValueError, RuntimeError):
            # Treat corrupt or incompatible persisted indexes like a cache miss.
            pass

    store = FAISS.from_documents(load_documents(), embeddings)
    try:
        store.save_local(str(INDEX_DIR))
    except Exception:
        pass
    return store


def format_documents(documents: list[Document]) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in documents)


def build_rag_chain(*, rebuild: bool = False, k: int = 5):
    """Chain over {"question", "chat_history"} returning "answer" and "documents"."""
    retriever = build_vectorstore(rebuild=rebuild).as_retriever(
        search_kwargs={"k": k}
    )
    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0.2, google_api_key=api_key)

    condense = (
        ChatPromptTemplate.from_messages(
            [
                ("system", CONDENSE_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{question}"),
            ]
        )
        | llm
        | StrOutputParser()
    )
    # A first question needs no rewriting, and rewriting it costs a round trip.
    search_query = RunnableBranch(
        (lambda x: bool(x.get("chat_history")), condense),
        RunnableLambda(lambda x: x["question"]),
    )

    answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ANSWER_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ]
    )

    return (
        RunnablePassthrough.assign(search_query=search_query)
        | RunnablePassthrough.assign(
            documents=lambda x: retriever.invoke(x["search_query"])
        )
        | RunnablePassthrough.assign(
            context=lambda x: format_documents(x["documents"])
        )
        | RunnablePassthrough.assign(
            answer=answer_prompt | llm | StrOutputParser()
        )
    )


class RagEngine:
    def __init__(self, chain):
        self.chain = chain

    def invoke(self, question: str, chat_history: list) -> dict:
        return self.chain.invoke({"question": question, "chat_history": chat_history})

    def stream(self, question: str, chat_history: list):
        result = self.invoke(question, chat_history)
        yield {"documents": result.get("documents", [])}
        yield {"answer": result.get("answer", "")}


def build_engine(*, rebuild: bool = False, k: int = DEFAULT_K) -> RagEngine:
    return RagEngine(build_rag_chain(rebuild=rebuild, k=k))


if __name__ == "__main__":
    chain = build_rag_chain()
    for question in [
        "How long do I have to return a laptop?",
        "Which gaming laptop do you recommend and is it in stock?",
    ]:
        result = chain.invoke({"question": question, "chat_history": []})
        print(f"\nQ: {question}\nA: {result['answer']}")
