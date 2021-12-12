__all__ = (
    "JinjaTemplateRenderer",
)

import typing as t
from datetime import datetime
from pathlib import Path

import stringcase  # type: ignore
from jinja2 import Environment, FileSystemLoader


class JinjaTemplateRenderer:
    def __init__(self, root: Path) -> None:
        self.__jinja_env = Environment(
            loader=FileSystemLoader(root),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.__jinja_env.filters.update({
            "snake_case": stringcase.snakecase,
            "pascal_case": stringcase.pascalcase,
            "sorted": self.__iter_sorted,
            "items_sorted_by_keys": self.__iter_items_sorted_by_keys,
            "datetime_iso": self.__convert_datetime_to_iso_format,
        })

    def __iter_sorted(self, values: object, attribute: str) -> t.Iterable[object]:
        if isinstance(values, t.Iterable):
            # FIXME: fix typing.
            yield from sorted(values, key=lambda v: getattr(v, attribute, 0))  # type: ignore

    def __iter_items_sorted_by_keys(self, values: object) -> t.Iterable[t.Tuple[object, object]]:
        if isinstance(values, t.Mapping):
            # FIXME: fix typing.
            yield from sorted(values.items(), key=lambda pair: pair[0])  # type: ignore

    def __convert_datetime_to_iso_format(self, value: object) -> str:
        if not isinstance(value, datetime):
            return ""

        return value.isoformat(timespec="seconds")

    def render(self, name: str, **kwargs: object) -> t.Iterable[str]:
        jinja_template = self.__jinja_env.get_template(f"{name}.jinja2")
        return jinja_template.stream(**kwargs)
