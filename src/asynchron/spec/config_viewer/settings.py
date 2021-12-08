__all__ = (
    "AsyncApiConfigViewSettings",
)

from dataclasses import dataclass


@dataclass(frozen=True)
class AsyncApiConfigViewSettings:
    show_null: bool = False
    sort_keys: bool = False
    prettified: bool = False
    indent: int = 0
