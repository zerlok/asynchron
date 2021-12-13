__all__ = (
    "MessageConsumerFunc",
    "MessageConsumer",
    "CallableMessageConsumer",
    "DecodedMessageConsumer",
    "MessageConsumerFactory",
)

import abc
import typing as t

from asynchron.core.message import MessageDecoder

T = t.TypeVar("T")
R = t.TypeVar("R")
B = t.TypeVar("B")
T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)


class MessageConsumerFunc(t.Protocol[T_contra]):
    async def __call__(self, message: T_contra) -> None: ...


class MessageConsumer(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def consume(self, message: T_contra) -> None:
        raise NotImplementedError


class CallableMessageConsumer(MessageConsumer[T_contra]):
    def __init__(self, consumer: MessageConsumerFunc[T_contra]) -> None:
        self.__consumer = consumer

    async def consume(self, message: T_contra) -> None:
        await self.__consumer(message)


class DecodedMessageConsumer(MessageConsumer[T_contra]):
    def __init__(self, decoder: MessageDecoder[T_contra, T], consumer: MessageConsumer[T]) -> None:
        self.__decoder = decoder
        self.__consumer = consumer

    async def consume(self, message: T_contra) -> None:
        decoded_message = self.__decoder.decode(message)
        await self.__consumer.consume(decoded_message)


class MessageConsumerFactory(t.Generic[T_contra, T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_consumer(self, settings: T_contra) -> MessageConsumer[T_co]:
        raise NotImplementedError
