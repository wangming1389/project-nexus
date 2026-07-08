from pathlib import Path
import shutil
from config import (
    CHROMA_DB_DIR,
    KNOWLEDGE_DIR,
)
from logger import setup_logger

logger = setup_logger(__name__)


def remove_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
        logger.info(f"Removed: {path}")
    else:
        logger.info(f"Skipped (not found): {path}")


def cleanup() -> None:
    logger.info("Starting cleanup...")

    remove_directory(KNOWLEDGE_DIR)
    remove_directory(CHROMA_DB_DIR)

    logger.info("Cleanup completed.")


if __name__ == "__main__":
    cleanup()