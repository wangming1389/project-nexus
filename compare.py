import json
from config import METADATA_FILE
from logger import setup_logger
from services.vector_db import get_collection

logger = setup_logger(__name__)


def load_metadata():
    with open(
        METADATA_FILE,
        encoding="utf-8",
    ) as f:
        return json.load(f)["articles"]


def load_indexed_hashes():
    collection = get_collection()
    result = collection.get(include=["metadatas"])
    hashes = {}

    for metadata in result["metadatas"]:
        article_id = metadata["article_id"]
        hashes.setdefault(
            article_id,
            metadata["content_hash"],
        )

    return hashes


def compare():
    metadata = load_metadata()
    indexed = load_indexed_hashes()
    new = []
    updated = []
    unchanged = []

    for article in metadata:
        article_id = article["id"]
        article_hash = article["content_hash"]

        if article_id not in indexed:
            new.append(article)
            continue

        if indexed[article_id] != article_hash:
            updated.append(article)
            continue

        unchanged.append(article)

    print()
    print(f"New       : {len(new)}")
    print(f"Updated   : {len(updated)}")
    print(f"Unchanged : {len(unchanged)}")


if __name__ == "__main__":
    compare()