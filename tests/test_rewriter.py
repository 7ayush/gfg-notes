"""Unit tests for the rewriter module.

Requirements: 6.1, 6.2
"""

import os

from gfg_scraper.rewriter import rewrite_links


class TestRewriteLinks:
    """Unit tests for rewrite_links post-processing."""

    # --- Scraped internal link rewritten to relative path (Req 6.1) ---

    def test_scraped_link_rewritten_to_relative_path(self, tmp_path):
        """A mapped internal URL should be replaced with a relative file path."""
        file_a = os.path.join(str(tmp_path), "01_arrays.md")
        file_b = os.path.join(str(tmp_path), "02_linked_list.md")

        url_a = "https://www.geeksforgeeks.org/arrays/"
        url_b = "https://www.geeksforgeeks.org/linked-list/"

        # file_a contains a link to url_b
        with open(file_a, "w", encoding="utf-8") as f:
            f.write(f"# Arrays\n\nSee [Linked List]({url_b}) for more.\n")
        with open(file_b, "w", encoding="utf-8") as f:
            f.write("# Linked List\n\nContent here.\n")

        mapping = {url_a: file_a, url_b: file_b}
        rewrite_links(mapping, str(tmp_path))

        with open(file_a, "r", encoding="utf-8") as f:
            content = f.read()

        expected_rel = os.path.relpath(file_b, os.path.dirname(file_a))
        assert expected_rel in content
        assert url_b not in content

    # --- Unscraped internal link retained as absolute URL (Req 6.2) ---

    def test_unscraped_link_retained_as_absolute_url(self, tmp_path):
        """An internal URL not in the mapping should remain unchanged."""
        file_a = os.path.join(str(tmp_path), "01_arrays.md")
        url_a = "https://www.geeksforgeeks.org/arrays/"
        unmapped_url = "https://www.geeksforgeeks.org/sorting-algorithms/"

        with open(file_a, "w", encoding="utf-8") as f:
            f.write(f"# Arrays\n\nSee [Sorting]({unmapped_url}) for details.\n")

        mapping = {url_a: file_a}
        rewrite_links(mapping, str(tmp_path))

        with open(file_a, "r", encoding="utf-8") as f:
            content = f.read()

        assert unmapped_url in content

    # --- File with no internal links remains unchanged (Req 6.1, 6.2) ---

    def test_file_with_no_links_unchanged(self, tmp_path):
        """A file containing no URLs from the mapping should not be modified."""
        file_a = os.path.join(str(tmp_path), "01_intro.md")
        url_a = "https://www.geeksforgeeks.org/intro/"

        original = "# Introduction\n\nNo links here, just plain text.\n"
        with open(file_a, "w", encoding="utf-8") as f:
            f.write(original)

        mapping = {url_a: file_a}
        rewrite_links(mapping, str(tmp_path))

        with open(file_a, "r", encoding="utf-8") as f:
            content = f.read()

        assert content == original

    # --- Multiple links: some mapped, some not ---

    def test_mixed_mapped_and_unmapped_links(self, tmp_path):
        """File with both mapped and unmapped URLs: mapped are rewritten, unmapped stay."""
        file_a = os.path.join(str(tmp_path), "01_arrays.md")
        file_b = os.path.join(str(tmp_path), "02_trees.md")

        url_a = "https://www.geeksforgeeks.org/arrays/"
        url_b = "https://www.geeksforgeeks.org/trees/"
        unmapped = "https://www.geeksforgeeks.org/graphs/"

        with open(file_a, "w", encoding="utf-8") as f:
            f.write(
                f"# Arrays\n\n"
                f"See [Trees]({url_b}) and [Graphs]({unmapped}).\n"
            )
        with open(file_b, "w", encoding="utf-8") as f:
            f.write("# Trees\n\nTree content.\n")

        mapping = {url_a: file_a, url_b: file_b}
        rewrite_links(mapping, str(tmp_path))

        with open(file_a, "r", encoding="utf-8") as f:
            content = f.read()

        expected_rel = os.path.relpath(file_b, os.path.dirname(file_a))
        assert expected_rel in content
        assert url_b not in content
        assert unmapped in content

    # --- Cross-directory relative paths ---

    def test_cross_directory_relative_paths(self, tmp_path):
        """Links between files in different subdirectories use correct relative paths."""
        dir_a = os.path.join(str(tmp_path), "topic_a")
        dir_b = os.path.join(str(tmp_path), "topic_b")
        os.makedirs(dir_a)
        os.makedirs(dir_b)

        file_a = os.path.join(dir_a, "01_sorting.md")
        file_b = os.path.join(dir_b, "01_searching.md")

        url_a = "https://www.geeksforgeeks.org/sorting/"
        url_b = "https://www.geeksforgeeks.org/searching/"

        with open(file_a, "w", encoding="utf-8") as f:
            f.write(f"# Sorting\n\nRelated: [Searching]({url_b})\n")
        with open(file_b, "w", encoding="utf-8") as f:
            f.write("# Searching\n\nContent.\n")

        mapping = {url_a: file_a, url_b: file_b}
        rewrite_links(mapping, str(tmp_path))

        with open(file_a, "r", encoding="utf-8") as f:
            content = f.read()

        expected_rel = os.path.relpath(file_b, os.path.dirname(file_a))
        assert expected_rel in content
        assert url_b not in content
        # Should contain "../topic_b/" style path
        assert ".." in expected_rel
