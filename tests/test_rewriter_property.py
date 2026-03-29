"""Property-based tests for the rewriter module.

Feature: gfg-web-scraper, Property 7: Link rewriting correctness
"""

import os

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from gfg_scraper.rewriter import rewrite_links

# ---------------------------------------------------------------------------
# Strategies for Property 7 – link rewriting correctness
# ---------------------------------------------------------------------------

# Generate URL path slugs for GfG-style URLs
_slug = st.from_regex(r"[a-z][a-z0-9\-]{2,30}", fullmatch=True)


@st.composite
def gfg_url(draw):
    """Generate a random GfG URL."""
    slug = draw(_slug)
    return f"https://www.geeksforgeeks.org/{slug}/"


@st.composite
def external_url(draw):
    """Generate a random external (non-GfG) URL that won't collide with mapped URLs."""
    slug = draw(_slug)
    domain = draw(st.sampled_from(["example.com", "wikipedia.org", "github.com"]))
    return f"https://{domain}/{slug}"


@st.composite
def url_to_filepath_mapping(draw, tmp_path_str):
    """Generate a random URL-to-filepath mapping with 2-5 pages and create files."""
    num_pages = draw(st.integers(min_value=2, max_value=5))
    urls = draw(
        st.lists(gfg_url(), min_size=num_pages, max_size=num_pages, unique=True)
    )

    mapping = {}
    for i, url in enumerate(urls):
        filepath = os.path.join(tmp_path_str, f"{i + 1:02d}_page_{i + 1}.md")
        mapping[url] = filepath

    return mapping


@st.composite
def rewriter_scenario(draw, tmp_path_str):
    """Generate a complete rewriter test scenario with files on disk."""
    mapping = draw(url_to_filepath_mapping(tmp_path_str))
    mapped_urls = list(mapping.keys())

    # Generate some unmapped external URLs
    num_unmapped = draw(st.integers(min_value=1, max_value=3))
    unmapped_urls = draw(
        st.lists(
            external_url(),
            min_size=num_unmapped,
            max_size=num_unmapped,
            unique=True,
        )
    )

    # For each page, generate Markdown content containing links to:
    # - some mapped URLs (should be rewritten)
    # - some unmapped URLs (should remain unchanged)
    file_contents = {}
    for url, filepath in mapping.items():
        lines = [f"# Page for {url}\n\n"]

        # Add links to other mapped URLs (not self)
        other_mapped = [u for u in mapped_urls if u != url]
        if other_mapped:
            chosen_mapped = draw(
                st.lists(
                    st.sampled_from(other_mapped),
                    min_size=1,
                    max_size=len(other_mapped),
                    unique=True,
                )
            )
            for linked_url in chosen_mapped:
                lines.append(f"See [linked article]({linked_url}) for more.\n\n")

        # Add links to unmapped URLs
        chosen_unmapped = draw(
            st.lists(
                st.sampled_from(unmapped_urls),
                min_size=1,
                max_size=len(unmapped_urls),
                unique=True,
            )
        )
        for ext_url in chosen_unmapped:
            lines.append(f"External reference: [link]({ext_url})\n\n")

        content = "".join(lines)
        file_contents[filepath] = content

        # Write the file to disk
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return mapping, file_contents, unmapped_urls


@given(data=st.data())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_link_rewriting_correctness(data, tmp_path):
    """Property 7: Link rewriting correctness.

    **Validates: Requirements 6.1, 6.2**

    For any Markdown file and URL-to-filepath mapping, after link rewriting:
    - Every internal GfG URL that exists in the mapping should be replaced
      with the correct relative file path.
    - Every URL that does NOT exist in the mapping should remain as the
      original absolute URL.
    """
    tmp_path_str = str(tmp_path)
    mapping, original_contents, unmapped_urls = data.draw(
        rewriter_scenario(tmp_path_str)
    )

    # Run the rewriter
    rewrite_links(mapping, tmp_path_str)

    # Verify each file
    for current_url, current_filepath in mapping.items():
        with open(current_filepath, "r", encoding="utf-8") as f:
            rewritten = f.read()

        # Check mapped URLs are rewritten to correct relative paths
        for target_url, target_filepath in mapping.items():
            if target_url == current_url:
                continue
            if target_url in original_contents[current_filepath]:
                expected_rel = os.path.relpath(
                    target_filepath, os.path.dirname(current_filepath)
                )
                assert target_url not in rewritten, (
                    f"Mapped URL {target_url} was NOT rewritten in {current_filepath}"
                )
                assert expected_rel in rewritten, (
                    f"Expected relative path {expected_rel} not found in {current_filepath}"
                )

        # Check unmapped URLs remain unchanged
        for ext_url in unmapped_urls:
            if ext_url in original_contents[current_filepath]:
                assert ext_url in rewritten, (
                    f"Unmapped URL {ext_url} was incorrectly modified in {current_filepath}"
                )
