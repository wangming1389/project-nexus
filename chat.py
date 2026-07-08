from google.genai import types
from config import (
    CHAT_MODEL,
    TOP_K,
)
from logger import setup_logger
from prompts import SYSTEM_PROMPT
from services.gemini import client
from services.vector_db import get_collection
from services.embedding import get_embedding_model

logger = setup_logger(__name__)


def embed_query(question: str) -> list[float]:
    """Embed the user's question into a vector using SentenceTransformer."""
    logger.info("Embedding query locally...")
    model = get_embedding_model()
    return model.encode(question).tolist()


def retrieve(question: str) -> list[dict]:
    """Retrieve the most relevant chunks from ChromaDB."""
    embedding = embed_query(question)

    logger.info("Searching knowledge base...")
    collection = get_collection()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        logger.warning("No relevant documents found.")
        return []

    retrieved = [
        {
            "document": doc,
            "metadata": meta,
            "distance": dist,
        }
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]

    logger.info(f"Retrieved {len(retrieved)} chunks.")
    return retrieved


def build_prompt(question: str, contexts: list[dict]) -> list[types.Content]:
    """
    Build the RAG prompt for Gemini.

    Each context block includes the chunk text and its source URL,
    so citations are always available regardless of chunk content.
    """
    separator = "\n\n" + "=" * 20 + "\n\n"

    context_blocks = []

    for i, item in enumerate(contexts, start=1):
        url = item["metadata"].get("url", "")
        title = item["metadata"].get("title", "")

        block_parts = [f"Document {i}"]
        if title:
            block_parts.append(f"Title: {title}")
        if url:
            block_parts.append(f"Article URL: {url}")

        block_parts.append(f"\n{item['document']}")

        block = "\n".join(block_parts)
        context_blocks.append(block)

    context = separator.join(context_blocks)

    prompt = f"""Use ONLY the context below to answer the user's question.
        If the answer cannot be found in the context, say you don't know.

        Context
        ========

        {context}

        ========

        Question:
        {question}""".strip()

    return [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    ]


def ask(question: str) -> str:
    """Execute the complete RAG pipeline and return a response."""
    contexts = retrieve(question)

    if not contexts:
        return "Sorry, I couldn't find any relevant documentation for your question."

    contents = build_prompt(question, contexts)

    logger.info("Generating response...")

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0,
        ),
    )

    if not response.text:
        return "Sorry, I couldn't generate a response."

    return response.text


def main():
    print("=" * 60)
    print("OptiBot - type 'exit' to quit.")
    print("=" * 60)

    while True:
        question = input("\nYou: ").strip()

        if not question:
            continue

        if question.lower() in {"exit", "quit"}:
            break

        try:
            print("\nOptiBot:\n")
            print(ask(question))
        except Exception as e:
            logger.exception(e)
            print("\nAn unexpected error occurred.")


if __name__ == "__main__":
    main()
