"""Shared text helpers for the TUI."""

from __future__ import annotations

import html
import re


def html_to_plain(text: str) -> str:
    """Convert HTML to plain text: strip tags, turn block/br into newlines, unescape entities."""
    if not text:
        return ""
    # Line/block breaks -> newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>\s*<p[^>]*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p\s*[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<div\s*[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities (&amp;, &lt;, etc.)
    text = html.unescape(text)
    return text.strip()
