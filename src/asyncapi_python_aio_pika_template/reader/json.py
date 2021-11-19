__all__ = (
    "JsonAsyncApiConfigReader",
)

import json
import typing as t

from asyncapi_python_aio_pika_template.app import AsyncApiConfigReader
from asyncapi_python_aio_pika_template.spec import AsyncAPIObject


# TODO: handle IO, yaml and pydantic errors
class JsonAsyncApiConfigReader(AsyncApiConfigReader):

    def read(self, source: t.TextIO) -> AsyncAPIObject:
        return AsyncAPIObject.parse_obj(json.load(source))
