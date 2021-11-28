__all__ = (
    "AsyncApiConfigTransformingConfigReader",
)

import typing as t

from asyncapi.app import AsyncApiConfigReader
from asyncapi.spec.base import AsyncAPIObject
from asyncapi.spec.transformer.base import AsyncApiConfigTransformer


class AsyncApiConfigTransformingConfigReader(AsyncApiConfigReader):

    def __init__(self, reader: AsyncApiConfigReader, transformers: t.Sequence[AsyncApiConfigTransformer]) -> None:
        self.__reader = reader
        self.__transformers = transformers

    def read(self, source: t.TextIO) -> AsyncAPIObject:
        config = self.__reader.read(source)

        for transformer in self.__transformers:
            config = transformer.transform(config)

        return config
