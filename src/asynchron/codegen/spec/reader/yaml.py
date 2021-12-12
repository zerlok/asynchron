__all__ = (
    "YamlAsyncApiConfigReader",
)

import typing as t

import yaml

from asynchron.codegen.app import AsyncApiConfigReader
from asynchron.codegen.spec.base import AsyncAPIObject


# TODO: handle IO, yaml and pydantic errors
class YamlAsyncApiConfigReader(AsyncApiConfigReader):

    def read(self, source: t.TextIO) -> AsyncAPIObject:
        return AsyncAPIObject.parse_obj(yaml.safe_load(source))  # type: ignore[misc]
