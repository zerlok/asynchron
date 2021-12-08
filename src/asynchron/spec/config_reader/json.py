__all__ = (
    "JsonAsyncApiConfigReader",
)

import json
import typing as t

from asynchron.app import AsyncApiConfigReader
from asynchron.spec.base import AsyncAPIObject


# TODO: handle IO, yaml and pydantic errors
class JsonAsyncApiConfigReader(AsyncApiConfigReader):

    def read(self, source: t.TextIO) -> AsyncAPIObject:
        return AsyncAPIObject.parse_obj(json.load(source))  # type: ignore[misc]
