import abc
import typing as t

from asynchron.core.consumer import MessageConsumer
from asynchron.core.message import MessageDecoder, MessageEncoder
from asynchron.core.publisher import MessagePublisher

T = t.TypeVar("T")
CM = t.TypeVar("CM")
CB = t.TypeVar("CB")
PM = t.TypeVar("PM")
PB = t.TypeVar("PB")


class Runnable(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError


class Controller(t.Generic[CM, CB, PM, PB], Runnable, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def bind_consumer(
            self,
            decoder: MessageDecoder[CM, T],
            consumer: MessageConsumer[T],
            bindings: CB,
    ) -> MessageConsumer[CM]:
        raise NotImplementedError

    @abc.abstractmethod
    def bind_publisher(
            self,
            encoder: MessageEncoder[T, PM],
            bindings: PB,
    ) -> MessagePublisher[T]:
        raise NotImplementedError
