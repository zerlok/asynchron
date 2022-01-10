__all__ = (
    "JinjaTemplateRenderer",
)

import typing as t
from datetime import datetime
from pathlib import Path

import stringcase  # type: ignore
from jinja2 import Environment, FileSystemLoader


class JinjaTemplateRenderer:
    @classmethod
    def from_template_root_dir(cls, root: Path) -> "JinjaTemplateRenderer":
        return cls(Environment(
            loader=FileSystemLoader(root),
            trim_blocks=True,
            lstrip_blocks=True,
        ))

    def __init__(self, jinja_env: Environment) -> None:
        self.__jinja_env = jinja_env
        self.__jinja_env.filters.update({
            "snakecase": self.__convert_to_snakecase,
            "pascalcase": self.__convert_to_pascalcase,
            "constcase": self.__convert_to_constcase,
            "find": self.__find,
            "sorted": self.__iter_sorted,
            "items_sorted_by_keys": self.__iter_items_sorted_by_keys,
            "datetime_iso": self.__convert_datetime_to_iso_format,
        })

    def render(
            self,
            name: str,
            context: t.Mapping[str, object],
    ) -> t.Iterable[str]:
        jinja_template = self.__jinja_env.get_template(f"{name}.jinja2")
        return jinja_template.stream(**context)

    def __convert_to_snakecase(self, value: object) -> str:
        if not isinstance(value, str) and isinstance(value, t.Iterable):
            return "_".join(stringcase.snakecase(str(item)) for item in value)

        return stringcase.snakecase(str(value))

    def __convert_to_pascalcase(self, value: object) -> str:
        if not isinstance(value, str) and isinstance(value, t.Iterable):
            return "".join(stringcase.pascalcase(str(item)) for item in value)

        return stringcase.pascalcase(str(value))

    def __convert_to_constcase(self, value: object) -> str:
        if not isinstance(value, str) and isinstance(value, t.Iterable):
            return "_".join(stringcase.constcase(str(item)) for item in value)

        return stringcase.constcase(str(value))

    def __iter_unique(self, items: object) -> t.Iterable[object]:
        if isinstance(items, t.Iterable):
            yield from set(items)

    def __find(self, items: object, attribute: str, value: object) -> t.Optional[object]:
        if isinstance(items, t.Iterable):
            for item in items:
                if getattr(item, attribute, None) == value:
                    return item

        return None

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
