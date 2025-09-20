"""Minimal type stubs for markdownify focusing on MarkdownConverter usage."""

from typing import Any, List, Optional, Union

from bs4 import BeautifulSoup, Tag

class MarkdownConverter:
    """HTML to Markdown converter with customizable conversion methods."""

    def __init__(
        self,
        *,
        heading_style: str = ...,
        strip: Optional[List[str]] = ...,
        escape_underscores: bool = ...,
        escape_asterisks: bool = ...,
        **options: Any
    ) -> None: ...

    def convert(self, html: Union[str, BeautifulSoup]) -> str:
        """Convert HTML string or BeautifulSoup object to Markdown."""
        ...

    def convert_pre(
        self,
        el: Tag,
        text: str,
        convert_as_inline: bool
    ) -> str:
        """Convert HTML pre elements to Markdown."""
        ...

    def should_convert_tag(self, tag: Tag) -> bool:
        """Determine if a tag should be converted."""
        ...

    def process_tag(self, tag: Tag) -> str:
        """Process an individual tag for conversion."""
        ...

# Convenience function for simple HTML to Markdown conversion
def markdownify(
    html: Union[str, BeautifulSoup],
    *,
    heading_style: str = ...,
    strip: Optional[List[str]] = ...,
    escape_underscores: bool = ...,
    escape_asterisks: bool = ...,
    **options: Any
) -> str: ...

__all__ = ["MarkdownConverter", "markdownify"]