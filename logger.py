import logging
import warnings


def setup_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger.
    """

    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        message=".*unauthenticated requests.*",
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

    return logging.getLogger(name)
