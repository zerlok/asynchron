__all__ = (
    "AsyncApiConfigReaderError",
    "AsyncApiConfigReader",
    "AsyncApiCodeGeneratorError",
    "AsyncApiCodeGenerator",
)

import abc
import typing as t
from pathlib import Path

from asyncapi_python_aio_pika_template.spec import AsyncAPIObject


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
    def generate(self, config: AsyncAPIObject) -> t.Iterable[t.Tuple[Path, t.TextIO]]:
        raise NotImplementedError
