import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import (
    KNOWLEDGE_DIR,
    METADATA_FILE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from logger import setup_logger
from services.vector_db import get_collection
from services.embedding import get_embedding_model

logger = setup_logger(__name__)

UPSERT_BATCH_SIZE = 200

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
)


def load_metadata() -> list[dict]:
    """Load article metadata produced by scrape.py."""
    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"{METADATA_FILE} not found. Please run scrape.py first."
        )

    with open(METADATA_FILE, encoding="utf-8") as f:
        articles = json.load(f).get("articles", [])

    logger.info(f"Loaded {len(articles)} articles from metadata.")
    return articles


def load_markdown(filename: str) -> str:
    """Read one markdown file from the knowledge directory."""
    filepath = KNOWLEDGE_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Markdown not found: {filepath}")

    return filepath.read_text(encoding="utf-8")


def split_article(article: dict, markdown: str) -> list[dict]:
    """
    Split one article into chunks.

    Title and URL are prepended to each chunk for grounding.
    Timestamps and hashes are kept in metadata only
    so they don't pollute the semantic vector.
    """
    chunks = text_splitter.split_text(markdown)

    results = [
        {
            "id": f"{article['id']}_{i}",
            "text": chunk.strip(),
            "metadata": {
                "article_id": article["id"],
                "title": article["title"],
                "url": article["url"],
                "chunk_index": i,
                "updated_at": article["updated_at"],
                "content_hash": article["content_hash"],
            },
        }
        for i, chunk in enumerate(chunks)
    ]

    logger.info(f"  '{article['title']}' → {len(results)} chunks")
    return results


def build_chunks(articles: list[dict]) -> list[dict]:
    """Chunk every article in the given list."""
    all_chunks = []

    for article in articles:
        try:
            markdown = load_markdown(article["slug"])
            all_chunks.extend(split_article(article, markdown))
        except Exception as e:
            logger.error(f"Skipping '{article['slug']}': {e}")

    logger.info(f"Total chunks built: {len(all_chunks)}")
    return all_chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed all chunks using the local SentenceTransformer model.
    """
    total = len(chunks)

    if not total:
        logger.warning("No chunks to embed.")
        return []

    logger.info(f"Embedding {total} chunks locally (this may take a moment)...")

    texts = [c["text"] for c in chunks]
    model = get_embedding_model()
    embeddings = model.encode(texts, batch_size=128, show_progress_bar=False)

    embedded: list[dict] = []
    for item, emb in zip(chunks, embeddings):
        embedded.append({**item, "embedding": emb.tolist()})

    return embedded


def get_existing_hashes() -> dict[int, str]:
    """Return {article_id: content_hash} for every indexed article."""
    logger.info("Reading existing index from ChromaDB...")
    collection = get_collection()

    result = collection.get(include=["metadatas"])

    hashes: dict[int, str] = {}
    for meta in result["metadatas"]:
        aid = meta["article_id"]
        if aid not in hashes:
            hashes[aid] = meta["content_hash"]

    logger.info(f"Found {len(hashes)} indexed articles.")
    return hashes


def delete_article(article_id: int):
    """Delete all chunks for one article (called before re-indexing)."""
    collection = get_collection()
    collection.delete(where={"article_id": article_id})
    logger.info(f"  Deleted chunks for article {article_id}.")


def upsert_chunks(chunks: list[dict]):
    """Write embedded chunks into ChromaDB in batches."""
    if not chunks:
        logger.warning("No chunks to upsert.")
        return

    total = len(chunks)
    logger.info(f"Upserting {total} chunks (batch={UPSERT_BATCH_SIZE})...")
    collection = get_collection()

    for start in range(0, total, UPSERT_BATCH_SIZE):
        batch = chunks[start : start + UPSERT_BATCH_SIZE]
        try:
            collection.upsert(
                ids=[c["id"] for c in batch],
                documents=[c["text"] for c in batch],
                embeddings=[c["embedding"] for c in batch],
                metadatas=[c["metadata"] for c in batch],
            )
            logger.info(f"Upserted {min(start + UPSERT_BATCH_SIZE, total)}/{total}")
        except Exception as e:
            logger.error(f"Upsert failed for batch {start}: {e}")

    logger.info("Upsert complete.")


def main():
    """
    Incremental indexing pipeline:
      1. Load metadata & existing hashes.
      2. Identify new/updated articles and delete stale chunks in one pass.
      3. Chunk -> Embed -> Upsert the required articles.
    """
    metadata = load_metadata()
    existing_hashes = get_existing_hashes()

    articles_to_index: list[dict] = []

    stats = {"new": 0, "updated": 0, "skipped": 0}

    for article in metadata:
        aid = article["id"]
        current_hash = article["content_hash"]

        if aid not in existing_hashes:
            articles_to_index.append(article)
            stats["new"] += 1

        elif existing_hashes[aid] != current_hash:
            delete_article(aid)
            articles_to_index.append(article)
            stats["updated"] += 1

        else:
            stats["skipped"] += 1

    logger.info(
        f"New: {stats['new']} | Updated: {stats['updated']} | Skipped: {stats['skipped']}"
    )

    if not articles_to_index:
        logger.info("Index is already up to date. Exiting.")
        return

    chunks = build_chunks(articles_to_index)
    embedded = embed_chunks(chunks)
    upsert_chunks(embedded)

    logger.info(
        f"Done - {len(articles_to_index)} articles indexed "
        f"({stats['new']} new, {stats['updated']} updated)."
    )


if __name__ == "__main__":
    main()
