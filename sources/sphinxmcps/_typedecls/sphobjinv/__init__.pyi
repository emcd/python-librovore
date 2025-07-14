"""Minimal type stubs for sphobjinv - only what we actually use."""

from collections.abc import Sequence
from typing import Any

class DataObjStr:
    """Sphinx inventory object data."""
    name: str
    domain: str
    role: str
    priority: str
    uri: str
    dispname: str

class Inventory:
    """Sphinx inventory containing project info and objects."""
    project: str
    version: str
    objects: Sequence[DataObjStr]
    
    def __init__(
        self, 
        *, 
        url: str | None = None,
        fname_zlib: str | None = None,
        **kwargs: Any
    ) -> None: ...