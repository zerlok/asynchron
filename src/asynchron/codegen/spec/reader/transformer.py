__all__ = (
    "AsyncApiConfigTransformingConfigReader",
)

import typing as t

from asynchron.codegen.app import AsyncApiConfigReader, AsyncApiConfigTransformer
from asynchron.codegen.spec.base import AsyncAPIObject


class AsyncApiConfigTransformingConfigReader(AsyncApiConfigReader):

    def __init__(self, reader: AsyncApiConfigReader, transformers: t.Sequence[AsyncApiConfigTransformer]) -> None:
        self.__reader = reader
        self.__transformers = transformers

    def read(self, source: t.TextIO) -> AsyncAPIObject:
        config = self.__reader.read(source)

        for transformer in self.__transformers:
            config = transformer.transform(config)

        return config
