from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
METADATA_FILE = KNOWLEDGE_DIR / "metadata.json"

CHAT_MODEL = "gemini-3.5-flash"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TEMPERATURE = 0.0
TOP_K = 5

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

COLLECTION_NAME = "optisigns_articles_st"

BASE_URL = "https://support.optisigns.com/api/v2/help_center/en-us"
PER_PAGE = 100
TIMEOUT = 15
