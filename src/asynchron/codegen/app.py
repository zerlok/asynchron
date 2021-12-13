__all__ = (
    "AsyncApiConfigReaderError",
    "AsyncApiConfigReader",
    "AsyncApiConfigTransformerError",
    "AsyncApiConfigTransformer",
    "AsyncApiConfigViewerError",
    "AsyncApiConfigViewer",
    "AsyncApiCodeGeneratorError",
    "AsyncApiCodeGenerator",
    "AsyncApiContentWriterError",
    "AsyncApiContentWriter",
)

import abc
import typing as t
from pathlib import Path

from asynchron.codegen.spec.base import AsyncAPIObject


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


class AsyncApiConfigViewerError(Exception):
    pass


class AsyncApiConfigViewer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def view(self, config: AsyncAPIObject) -> None:
        raise NotImplementedError


class AsyncApiCodeGeneratorError(Exception):
    pass


class AsyncApiCodeGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.Iterable[str]]]:
        raise NotImplementedError


class AsyncApiContentWriterError(Exception):
    pass


class AsyncApiContentWriter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def write(self, content: t.Iterable[t.Tuple[Path, t.Iterable[str]]]) -> None:
        raise NotImplementedError
