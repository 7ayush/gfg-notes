"""Image downloading module for saving article images locally."""

import hashlib
import logging
import os
from urllib.parse import urlparse

import requests

from gfg_scraper.config import ScraperConfig

logger = logging.getLogger(__name__)

# Reuse the same User-Agent as the fetcher
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def download_images(article_soup, output_dir: str, file_path: str, config: ScraperConfig) -> None:
    """Download images from article HTML and rewrite src to local paths.

    Images are saved to ``{output_dir}/src/`` with a hash-based filename
    to avoid collisions.  The ``<img>`` tags in *article_soup* are modified
    in-place so that subsequent Markdown conversion references local files.
    """
    src_dir = os.path.join(output_dir, "src")
    imgs = article_soup.find_all("img", src=True)
    if not imgs:
        return

    os.makedirs(src_dir, exist_ok=True)

    for img in imgs:
        src = img["src"].strip()
        if not src or src.startswith("data:"):
            continue

        # Build a unique filename from the URL
        url_hash = hashlib.md5(src.encode()).hexdigest()[:10]
        parsed = urlparse(src)
        ext = os.path.splitext(parsed.path)[1] or ".png"
        local_name = f"{url_hash}{ext}"
        local_path = os.path.join(src_dir, local_name)

        # Download if not already cached
        if not os.path.exists(local_path):
            try:
                resp = requests.get(
                    src,
                    headers={"User-Agent": _USER_AGENT},
                    timeout=config.request_timeout,
                    stream=True,
                )
                if resp.ok:
                    with open(local_path, "wb") as f:
                        for chunk in resp.iter_content(8192):
                            f.write(chunk)
                else:
                    logger.warning("Failed to download image %s (status %d)", src, resp.status_code)
                    continue
            except Exception:
                logger.warning("Error downloading image %s", src, exc_info=True)
                continue

        # Rewrite the img src to a relative path from the markdown file
        rel_path = os.path.relpath(local_path, os.path.dirname(file_path))
        img["src"] = rel_path
