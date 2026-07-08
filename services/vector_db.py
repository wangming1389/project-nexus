import chromadb

from config import (
    CHROMA_DB_DIR,
    COLLECTION_NAME,
)

def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "OptiSigns Knowledge Base"},
    )
