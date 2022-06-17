__all__ = (
    "AsyncApiConfigReaderError",
    "AsyncApiConfigReader",
    "AsyncApiConfigTransformerError",
    "AsyncApiConfigTransformer",
    "AsyncApiConfigViewerError",
    "AsyncApiConfigViewer",
    "AsyncApiCodeGeneratorError",
    "AsyncApiCodeGeneratorContent",
    "AsyncApiCodeGenerator",
    "AsyncApiContentWriterError",
    "AsyncApiContentWriter",
)

import abc
import typing as t
from pathlib import Path

from asynchron.codegen.spec.asyncapi import AsyncAPIObject


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


class AsyncApiCodeGeneratorContent(t.Collection[t.Tuple[Path, t.Sequence[str]]]):

    def __init__(self, content_by_paths: t.Optional[t.Mapping[Path, t.Sequence[str]]] = None) -> None:
        self.__content_by_paths: t.Dict[Path, t.Sequence[str]] = dict(content_by_paths or {})

    def __contains__(self, __x: object) -> bool:
        return __x in self.__content_by_paths

    def __len__(self) -> int:
        return len(self.__content_by_paths)

    def __iter__(self) -> t.Iterator[t.Tuple[Path, t.Sequence[str]]]:
        yield from self.__content_by_paths.items()


class AsyncApiCodeGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate(self, config: AsyncAPIObject) -> AsyncApiCodeGeneratorContent:
        raise NotImplementedError


class AsyncApiContentWriterError(Exception):
    pass


class AsyncApiContentWriter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def write(self, content: AsyncApiCodeGeneratorContent) -> None:
        raise NotImplementedError
