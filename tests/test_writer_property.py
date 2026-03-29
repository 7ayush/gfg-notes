"""Property-based tests for the writer module.

Feature: gfg-web-scraper, Property 8: Filename generation produces valid numbered slugs with .md extension
"""

import os
import re

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from gfg_scraper.writer import build_file_path

# ---------------------------------------------------------------------------
# Strategies for Property 8 – filename generation
# ---------------------------------------------------------------------------

# Generate URL path slugs with various characters (alphanumeric, hyphens,
# underscores, dots, and other special chars that might appear in URL paths)
_slug_chars = st.from_regex(r"[a-zA-Z0-9\-_.~!@%&+,;:]{1,60}", fullmatch=True)

_discovery_orders = st.integers(min_value=1, max_value=999)


@st.composite
def random_gfg_url(draw):
    """Generate a random GfG-style URL with a path slug."""
    slug = draw(_slug_chars)
    # Optionally add a trailing slash
    trailing = draw(st.sampled_from(["", "/"]))
    return f"https://www.geeksforgeeks.org/{slug}{trailing}"


@given(url=random_gfg_url(), discovery_order=_discovery_orders)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_filename_generation_produces_valid_numbered_slugs(url, discovery_order, tmp_path):
    """Property 8: Filename generation produces valid numbered slugs with .md extension.

    **Validates: Requirements 2.2, 7.2, 7.3**

    For any URL path slug and discovery order number, the generated filename should:
    (a) start with a zero-padded discovery order number (at least 2 digits),
    (b) contain only alphanumeric characters and underscores in the slug portion,
    (c) end with the .md extension.
    """
    parent_dir = str(tmp_path)
    file_path = build_file_path(url, parent_dir, discovery_order)
    filename = os.path.basename(file_path)

    # (c) Must end with .md
    assert filename.endswith(".md"), f"Filename does not end with .md: {filename}"

    # Strip the .md extension for further checks
    stem = filename[:-3]

    # The stem should be: <zero-padded number>_<slug>
    # (a) Starts with a zero-padded number (at least 2 digits)
    match = re.match(r"^(\d{2,})_(.+)$", stem)
    assert match is not None, (
        f"Filename stem does not match expected pattern '<padded_number>_<slug>': {stem}"
    )

    padded_number = match.group(1)
    slug_part = match.group(2)

    # The padded number should equal the discovery order
    assert int(padded_number) == discovery_order, (
        f"Padded number {padded_number} does not match discovery_order {discovery_order}"
    )

    # (b) Slug portion contains only alphanumeric characters and underscores
    assert re.fullmatch(r"[a-zA-Z0-9_]+", slug_part), (
        f"Slug portion contains invalid characters: {slug_part}"
    )
