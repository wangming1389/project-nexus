from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL
from logger import setup_logger

logger = setup_logger(__name__)

_model = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading local embedding model...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model
