from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Any
import requests
from markdownify import markdownify as md
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import (
    BASE_URL,
    KNOWLEDGE_DIR,
    METADATA_FILE,
    PER_PAGE,
    TIMEOUT,
)
from logger import setup_logger

logger = setup_logger(__name__)

KNOWLEDGE_DIR.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "OptiBot-Scraper/1.0"})

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    allowed_methods=["GET"],
    status_forcelist=[
        429,
        500,
        502,
        503,
        504,
    ],
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("http://", adapter)
session.mount("https://", adapter)


def clean_slug(title: str) -> str:
    """
    Convert article title into a filesystem-safe filename.
    """

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        title.lower(),
    ).strip("-")

    return f"{slug}.md"


def calculate_hash(text: str) -> str:
    """
    Calculate SHA256 hash of article body.
    Used later by compare.py.
    """

    return sha256(text.encode("utf-8")).hexdigest()


def fetch_json(url: str) -> dict[str, Any]:
    """
    Fetch JSON from Zendesk API.
    """

    response = session.get(
        url,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


def fetch_all_articles() -> list[dict]:
    """
    Fetch every article using Zendesk pagination.
    """

    url = f"{BASE_URL}/articles.json?per_page={PER_PAGE}"
    articles = []

    while url:
        logger.info(f"Fetching: {url}")
        data = fetch_json(url)
        articles.extend(data.get("articles", []))
        url = data.get("next_page")

    articles.sort(key=lambda article: article.get("id", 0))

    return articles


def article_to_markdown(article: dict) -> str:
    """
    Convert one Zendesk article to Markdown.
    """

    title = article.get("title", "Untitled")
    body = article.get("body", "")
    markdown_body = md(
        body,
        heading_style="ATX",
    )

    return f"""# {title}
        {markdown_body}
        ---
        Article ID: {article.get("id")}
        Section ID: {article.get("section_id")}
        Updated At: {article.get("updated_at")}
        Article URL: {article.get("html_url")}
    """


def build_metadata(article: dict) -> dict:
    """
    Build metadata for metadata.json.
    """

    body = article.get("body", "")
    slug = clean_slug(article.get("title", "Untitled"))

    return {
        "id": article.get("id"),
        "title": article.get("title"),
        "slug": slug,
        "section_id": article.get("section_id"),
        "created_at": article.get("created_at"),
        "updated_at": article.get("updated_at"),
        "url": article.get("html_url"),
        "content_hash": calculate_hash(body),
    }


def save_metadata(
    metadata: list[dict],
    stats: dict,
) -> None:
    """
    Save metadata.json.
    """

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(metadata),
        "saved": stats["saved"],
        "skipped": stats["skipped"],
        "failed": stats["failed"],
        "articles": metadata,
    }

    METADATA_FILE.write_text(
        json.dumps(
            payload,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    logger.info(f"Metadata saved: {METADATA_FILE}")


def save_article(
    article: dict,
    filename: str,
) -> Path:
    """
    Save one article as Markdown.
    """

    filepath = KNOWLEDGE_DIR / filename

    markdown = article_to_markdown(article)

    filepath.write_text(
        markdown,
        encoding="utf-8",
    )

    logger.info(f"Saved: {filename}")

    return filepath


def main():
    logger.info("Fetching articles...")
    articles = fetch_all_articles()

    logger.info(f"Found {len(articles)} articles.")
    metadata = []
    stats = {
        "saved": 0,
        "skipped": 0,
        "failed": 0,
    }

    for article in articles:
        title = article.get(
            "title",
            "Untitled",
        )
        if not article.get("body"):
            logger.warning(f"Skipped (empty body): {title}")

            stats["skipped"] += 1
            continue

        try:
            metadata_item = build_metadata(article)
            save_article(
                article,
                metadata_item["slug"],
            )

            metadata.append(metadata_item)

            stats["saved"] += 1

        except Exception as e:
            logger.error(f"Failed: {title} ({e})")

            stats["failed"] += 1

    save_metadata(
        metadata,
        stats,
    )

    logger.info("Summary")
    logger.info(f"Saved    : {stats['saved']}")
    logger.info(f"Skipped  : {stats['skipped']}")
    logger.info(f"Failed   : {stats['failed']}")
    logger.info(f"Metadata : {METADATA_FILE}")


if __name__ == "__main__":
    main()
