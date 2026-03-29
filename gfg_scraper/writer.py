"""File writer module for saving scraped Markdown content."""

import os
import re
from urllib.parse import urlparse


def build_file_path(url: str, parent_dir: str, discovery_order: int) -> str:
    """
    Build the local file path for a scraped URL.
    Derives filename from URL slug, prepends zero-padded discovery order.
    Creates parent directories as needed.
    Returns the full file path.
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Take the last non-empty segment as the slug
    segments = [s for s in path.split("/") if s]
    slug = segments[-1] if segments else ""

    # Replace hyphens and non-alphanumeric characters with underscores
    slug = re.sub(r"[^a-zA-Z0-9]", "_", slug)

    # Collapse multiple consecutive underscores
    slug = re.sub(r"_+", "_", slug)

    # Strip leading/trailing underscores
    slug = slug.strip("_")

    # Fallback if slug is empty
    if not slug:
        slug = "index"

    # Zero-padded discovery order (minimum 2 digits)
    padded = f"{discovery_order:02d}"

    filename = f"{padded}_{slug}.md"

    os.makedirs(parent_dir, exist_ok=True)

    return os.path.join(parent_dir, filename)

def save_markdown(file_path: str, content: str) -> None:
    """Write Markdown content to the given file path."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

