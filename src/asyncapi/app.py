__all__ = (
    "AsyncApiConfigReaderError",
    "AsyncApiConfigReader",
    "AsyncApiConfigTransformerError",
    "AsyncApiConfigTransformer",
    "AsyncApiCodeGeneratorError",
    "AsyncApiCodeGenerator",
    "read_config",
)

import abc
import typing as t
from pathlib import Path

from asyncapi.spec.base import AsyncAPIObject


class AsyncApiConfigReaderError(Exception):
    pass


class AsyncApiConfigReader(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def read(self, source: t.TextIO) -> AsyncAPIObject:
        raise NotImplementedError


class AsyncApiConfigTransformerError(Exception):
    pass


class AsyncApiConfigTransformer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        raise NotImplementedError


class AsyncApiCodeGeneratorError(Exception):
    pass


class AsyncApiCodeGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        raise NotImplementedError


def read_config(
        source: t.TextIO,
        reader: AsyncApiConfigReader,
        transformers: t.Sequence[AsyncApiConfigTransformer],
) -> AsyncAPIObject:
    config = reader.read(source)

    for transformer in transformers:
        config = transformer.transform(config)

    return config
