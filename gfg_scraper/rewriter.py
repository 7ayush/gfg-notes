"""Link rewriter module for post-processing saved Markdown files."""

import os


def rewrite_links(url_to_filepath: dict[str, str], output_dir: str) -> None:
    """
    For each saved Markdown file, replace internal GfG URLs
    with relative paths to local files where the target was scraped.
    Retains original URLs for pages not scraped.
    """
    for current_url, current_filepath in url_to_filepath.items():
        if not os.path.isfile(current_filepath):
            continue

        with open(current_filepath, "r", encoding="utf-8") as f:
            content = f.read()

        updated = content
        for target_url, target_filepath in url_to_filepath.items():
            if target_url == current_url:
                continue
            if target_url not in updated:
                continue
            relative_path = os.path.relpath(
                target_filepath, os.path.dirname(current_filepath)
            )
            updated = updated.replace(target_url, relative_path)

        if updated != content:
            with open(current_filepath, "w", encoding="utf-8") as f:
                f.write(updated)
