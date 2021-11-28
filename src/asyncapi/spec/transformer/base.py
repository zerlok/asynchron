__all__ = (
    "AsyncApiConfigTransformerError",
    "AsyncApiConfigTransformer",
)

import abc

from asyncapi.spec.base import AsyncAPIObject


class AsyncApiConfigTransformerError(Exception):
    pass


class AsyncApiConfigTransformer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def transform(self, config: AsyncAPIObject) -> AsyncAPIObject:
        raise NotImplementedError
