import json
import logging
import os
import re
import time
from pathlib import Path

from groq import Groq
import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_required_env(name: str) -> str:
    """Get required environment variable or exit with helpful error."""
    value = os.getenv(name)
    if not value:
        logger.error(f"Missing required environment variable: {name}")
        logger.error(f"Please set {name} in your .env file. See .env.example")
        raise SystemExit(1)
    return value


CURIUS_USER_ID = get_required_env("CURIUS_USER_ID")
CURIUS_API_URL = f"https://curius.app/api/users/{CURIUS_USER_ID}/links"
VAULT_PATH = Path(get_required_env("VAULT_PATH"))
STATE_FILE = Path(__file__).parent / "processed_links.json"


def fetch_curius_links() -> list[dict]:
    """Fetch all saved links from Curius API."""
    logger.info("Fetching links from Curius...")
    response = httpx.get(CURIUS_API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
    links = data.get("userSaved", [])
    logger.info(f"Found {len(links)} total links")
    return links


def load_processed_ids() -> set[int]:
    """Load the set of already-processed link IDs."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_processed_ids(ids: set[int]) -> None:
    """Save the set of processed link IDs."""
    with open(STATE_FILE, "w") as f:
        json.dump(list(ids), f)


def filter_new_links(links: list[dict], processed_ids: set[int]) -> list[dict]:
    """Filter out already-processed links."""
    new_links = [link for link in links if link["id"] not in processed_ids]
    logger.info(f"Found {len(new_links)} new links to process")
    return new_links


def summarize_with_llm(text: str, title: str) -> str:
    """Summarize text using Groq API with Gemma 3 27B."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=api_key)

    prompt = f"""Summarize the following article in 2-3 concise paragraphs. Focus on the key insights and main points.

Title: {title}

Content:
{text[:15000]}"""  # Truncate to avoid token limits

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                logger.warning(f"Groq API error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to summarize after {max_retries} attempts: {e}")
                return "[Summary unavailable]"


def sanitize_filename(title: str) -> str:
    """Sanitize title for use as filename."""
    sanitized = re.sub(r'[<>:"/\\|?*]', "", title)
    sanitized = sanitized.strip()
    sanitized = sanitized[:100]  # Limit length
    return sanitized or "Untitled"


def create_markdown(link: dict, summary: str) -> str:
    """Create markdown content for a link."""
    title = link.get("title", "Untitled")
    url = link.get("link", "")
    author = link.get("metadata", {}).get("author", "") if link.get("metadata") else ""
    date_saved = link.get("createdDate", "")[:10] if link.get("createdDate") else ""
    curius_id = link.get("id", "")
    favorite = link.get("favorite", False)

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f"url: {url}",
    ]
    if author:
        frontmatter_lines.append(f"author: {author}")
    if date_saved:
        frontmatter_lines.append(f"date_saved: {date_saved}")
    frontmatter_lines.extend([
        f"curius_id: {curius_id}",
        f"favorite: {str(favorite).lower()}",
        "---",
    ])
    frontmatter = "\n".join(frontmatter_lines)

    # Build content
    content_parts = [frontmatter, "", f"# {title}", "", "## Summary", summary]

    # Add highlights
    highlights = link.get("highlights", [])
    if highlights:
        content_parts.extend(["", "## Highlights"])
        for h in highlights:
            highlight_text = h.get("highlight", "")
            if highlight_text:
                content_parts.append(f"\n> \"{highlight_text}\"")

    # Add comments
    comments = link.get("comments", [])
    if comments:
        content_parts.extend(["", "## Comments"])
        for c in comments:
            comment_text = c.get("comment", "")
            if comment_text:
                content_parts.append(f"- {comment_text}")

    # Add source link
    content_parts.extend(["", "## Source", f"[Original Article]({url})"])

    return "\n".join(content_parts)


def save_to_vault(title: str, content: str, curius_id: int) -> Path:
    """Save markdown content to the Obsidian vault."""
    VAULT_PATH.mkdir(parents=True, exist_ok=True)

    filename = sanitize_filename(title) + ".md"
    filepath = VAULT_PATH / filename

    # Handle filename collision
    if filepath.exists():
        filename = f"{sanitize_filename(title)} ({curius_id}).md"
        filepath = VAULT_PATH / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def main():
    logger.info("Starting Curius to Obsidian sync...")

    # Fetch links
    links = fetch_curius_links()

    # Filter to new links
    processed_ids = load_processed_ids()
    new_links = filter_new_links(links, processed_ids)

    if not new_links:
        logger.info("No new links to process. Done!")
        return

    # Process each link
    for i, link in enumerate(new_links, 1):
        title = link.get("title", "Untitled")
        link_id = link["id"]
        logger.info(f"Processing [{i}/{len(new_links)}]: {title}")

        # Get text to summarize
        full_text = ""
        if link.get("metadata") and link["metadata"].get("full_text"):
            full_text = link["metadata"]["full_text"]
        elif link.get("snippet"):
            full_text = link["snippet"]

        if not full_text:
            logger.warning(f"No content available for '{title}', skipping summary")
            summary = "[No content available for summarization]"
        else:
            summary = summarize_with_llm(full_text, title)

        # Create and save markdown
        markdown = create_markdown(link, summary)
        filepath = save_to_vault(title, markdown, link_id)
        logger.info(f"Saved: {filepath}")

        # Update state after each successful save
        processed_ids.add(link_id)
        save_processed_ids(processed_ids)

        # Small delay to be nice to Gemini API
        time.sleep(1)

    logger.info(f"Done! Processed {len(new_links)} new links.")


if __name__ == "__main__":
    main()
