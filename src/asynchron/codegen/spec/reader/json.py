__all__ = (
    "JsonAsyncApiConfigReader",
)

import json
import typing as t

from asynchron.codegen.app import AsyncApiConfigReader
from asynchron.codegen.spec.base import AsyncAPIObject


# TODO: handle IO, yaml and pydantic errors
class JsonAsyncApiConfigReader(AsyncApiConfigReader):

    def read(self, source: t.TextIO) -> AsyncAPIObject:
        return AsyncAPIObject.parse_obj(json.load(source))  # type: ignore[misc]
