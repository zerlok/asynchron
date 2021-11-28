__all__ = (
    "YamlAsyncApiConfigReader",
)

import typing as t

import yaml

from asyncapi.app import AsyncApiConfigReader
from asyncapi.spec.base import AsyncAPIObject


# TODO: handle IO, yaml and pydantic errors
class YamlAsyncApiConfigReader(AsyncApiConfigReader):

    def read(self, source: t.TextIO) -> AsyncAPIObject:
        return AsyncAPIObject.parse_obj(yaml.safe_load(source))  # type: ignore[misc]
