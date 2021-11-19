__all__ = (
    "YamlAsyncApiConfigReader",
)

import typing as t

import yaml

from asyncapi_python_aio_pika_template.app import AsyncApiConfigReader
from asyncapi_python_aio_pika_template.spec import AsyncAPIObject


# TODO: handle IO, yaml and pydantic errors
class YamlAsyncApiConfigReader(AsyncApiConfigReader):

    def read(self, source: t.TextIO) -> AsyncAPIObject:
        return AsyncAPIObject.parse_obj(yaml.safe_load(source))
