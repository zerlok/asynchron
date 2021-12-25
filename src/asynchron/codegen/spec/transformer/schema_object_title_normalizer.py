__all__ = (
    "SchemaObjectTitleNormalizingTransformer",
)

import re
import typing as t

import stringcase

from asynchron.codegen.app import AsyncApiConfigTransformer
from asynchron.codegen.spec.base import AsyncAPIObject, SchemaObject
from asynchron.codegen.spec.walker.spec_object_path import SpecObjectWithPathWalker
from asynchron.serializable_object_modifier import SerializableObjectModifier
from asynchron.strict_typing import as_


class SchemaObjectTitleNormalizingTransformer(AsyncApiConfigTransformer):

    def __init__(
            self,
            modifier: t.Optional[SerializableObjectModifier] = None,
    ) -> None:
        self.__modifier = modifier or SerializableObjectModifier()
        self.__walker = SpecObjectWithPathWalker.create_bfs()

    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        changes: t.List[t.Tuple[t.Sequence[t.Union[int, str]], str]] = []

        for path, obj in self.__walker.walk(config):
            if schema := as_(SchemaObject, obj):
                if title := schema.title:
                    normalized_name = self.__normalize_name((title,))
                else:
                    normalized_name = self.__normalize_name(tuple(str(part) for part in path))

                if normalized_name != schema.title:
                    changes.append(((*path, "title"), normalized_name))

        return self.__modifier.replace(config, changes)

    def __normalize_name(self, value: t.Sequence[str]) -> str:
        x = re.sub(r"[^A-Za-z0-9_]+", "_", "_".join(value))
        x = stringcase.snakecase(x)
        x = re.sub(r"_+", "_", x)
        x = re.sub(r"^_?(.*?)_$", "\1", x)

        return x
