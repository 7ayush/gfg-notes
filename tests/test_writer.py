"""Unit tests for the writer module."""

import os

from gfg_scraper.writer import build_file_path, save_markdown


def test_save_markdown_writes_content(tmp_path):
    """Test that save_markdown writes the given content to the file."""
    file_path = os.path.join(tmp_path, "test.md")
    content = "# Hello\n\nSome markdown content."

    save_markdown(file_path, content)

    with open(file_path, "r", encoding="utf-8") as f:
        assert f.read() == content


def test_save_markdown_uses_utf8(tmp_path):
    """Test that save_markdown correctly handles UTF-8 characters."""
    file_path = os.path.join(tmp_path, "unicode.md")
    content = "# Ünïcödé\n\nCafé, naïve, résumé, 日本語"

    save_markdown(file_path, content)

    with open(file_path, "r", encoding="utf-8") as f:
        assert f.read() == content


def test_save_markdown_overwrites_existing(tmp_path):
    """Test that save_markdown overwrites an existing file."""
    file_path = os.path.join(tmp_path, "overwrite.md")

    save_markdown(file_path, "old content")
    save_markdown(file_path, "new content")

    with open(file_path, "r", encoding="utf-8") as f:
        assert f.read() == "new content"


def test_save_markdown_empty_content(tmp_path):
    """Test that save_markdown handles empty content."""
    file_path = os.path.join(tmp_path, "empty.md")

    save_markdown(file_path, "")

    with open(file_path, "r", encoding="utf-8") as f:
        assert f.read() == ""


# ---------------------------------------------------------------------------
# Tests for build_file_path  (Requirements 7.1, 7.2, 7.3, 7.4)
# ---------------------------------------------------------------------------


class TestBuildFilePath:
    """Unit tests for build_file_path filename generation."""

    # --- Filename derivation from URL slugs (Req 7.3) ---

    def test_simple_slug(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org/arrays", str(tmp_path), 1
        )
        assert os.path.basename(path) == "01_arrays.md"

    def test_hyphenated_slug_replaced_with_underscores(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org/linked-list", str(tmp_path), 1
        )
        assert os.path.basename(path) == "01_linked_list.md"

    def test_special_characters_replaced_with_underscores(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org/c++.basics!@intro", str(tmp_path), 1
        )
        filename = os.path.basename(path)
        # Special chars become underscores; consecutive underscores collapsed
        assert filename == "01_c_basics_intro.md"

    def test_trailing_slash_ignored(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org/arrays/", str(tmp_path), 1
        )
        assert os.path.basename(path) == "01_arrays.md"

    def test_root_url_falls_back_to_index(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org/", str(tmp_path), 1
        )
        assert os.path.basename(path) == "01_index.md"

    def test_root_url_no_trailing_slash(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org", str(tmp_path), 1
        )
        assert os.path.basename(path) == "01_index.md"

    # --- Zero-padding (Req 7.2) ---

    def test_zero_padding_single_digit(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org/arrays", str(tmp_path), 1
        )
        assert os.path.basename(path).startswith("01_")

    def test_zero_padding_two_digits(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org/arrays", str(tmp_path), 99
        )
        assert os.path.basename(path).startswith("99_")

    def test_zero_padding_three_digits(self, tmp_path):
        path = build_file_path(
            "https://www.geeksforgeeks.org/arrays", str(tmp_path), 100
        )
        assert os.path.basename(path).startswith("100_")

    # --- Directory creation (Req 7.4) ---

    def test_creates_parent_directory(self, tmp_path):
        new_dir = os.path.join(str(tmp_path), "nested", "deep")
        build_file_path(
            "https://www.geeksforgeeks.org/arrays", new_dir, 1
        )
        assert os.path.isdir(new_dir)

    def test_existing_directory_no_error(self, tmp_path):
        """Calling build_file_path twice with the same parent_dir should not raise."""
        parent = str(tmp_path)
        build_file_path("https://www.geeksforgeeks.org/a", parent, 1)
        build_file_path("https://www.geeksforgeeks.org/b", parent, 2)

    # --- Full path correctness (Req 7.1) ---

    def test_full_path_joins_parent_and_filename(self, tmp_path):
        parent = str(tmp_path)
        path = build_file_path(
            "https://www.geeksforgeeks.org/data-structures", parent, 3
        )
        assert path == os.path.join(parent, "03_data_structures.md")
