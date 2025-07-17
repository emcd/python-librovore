"""Minimal type stubs for BeautifulSoup focusing on our usage."""

from typing import Any, Dict, Optional, Union, List
from .element import Tag, NavigableString, PageElement
from ._warnings import (
    AttributeResemblesVariableWarning,
    GuessedAtParserWarning,
    MarkupResemblesLocatorWarning,
    UnusualUsageWarning,
    XMLParsedAsHTMLWarning,
)

__all__ = [
    "BeautifulSoup",
    "Tag",
    "NavigableString",
    "PageElement",
    "AttributeResemblesVariableWarning",
    "GuessedAtParserWarning", 
    "MarkupResemblesLocatorWarning",
    "UnusualUsageWarning",
    "XMLParsedAsHTMLWarning",
]

class BeautifulSoup(Tag):
    """A BeautifulSoup object representing a parsed HTML/XML document."""
    
    def __init__(
        self,
        markup: Union[str, bytes] = ...,
        features: Optional[Union[str, List[str]]] = ...,
        **kwargs: Any
    ) -> None: ...