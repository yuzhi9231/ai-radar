"""URL handling for collected article links."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

# Permalinks whose first path segment is a date are written as /YYYY/MM/DD/slug/.
# Rows written before this module stored them as /YYYY-MM-DD/slug/, which 404s.
DATE_SEGMENT = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def normalize_article_url(url: str) -> str:
    """Rewrite a dash-form date segment as the slash form the site actually serves."""
    if not url:
        return url

    parts = urlsplit(url)
    segments = parts.path.split("/")
    if len(segments) < 2:
        return url

    match = DATE_SEGMENT.match(segments[1])
    if not match:
        return url

    segments[1] = "/".join(match.groups())
    return urlunsplit(
        (parts.scheme, parts.netloc, "/".join(segments), parts.query, parts.fragment)
    )


def looks_uncanonical(url: str) -> bool:
    """True when the URL still carries a dash-form date segment."""
    segments = urlsplit(url).path.split("/")
    return len(segments) >= 2 and bool(DATE_SEGMENT.match(segments[1]))
