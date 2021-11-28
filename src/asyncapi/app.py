__all__ = (
    "AsyncApiConfigReaderError",
    "AsyncApiConfigReader",
    "AsyncApiCodeGeneratorError",
    "AsyncApiCodeGenerator",
    "AsyncApiCodeWriterError",
    "AsyncApiCodeWriter",
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


class AsyncApiCodeGeneratorError(Exception):
    pass


class AsyncApiCodeGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        raise NotImplementedError


class AsyncApiCodeWriterError(Exception):
    pass


class AsyncApiCodeWriter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def write(self, path: Path, content: t.Iterable[str]) -> None:
        raise NotImplementedError
