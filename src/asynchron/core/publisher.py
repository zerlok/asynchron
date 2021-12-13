import abc
import typing as t

from asynchron.core.message import MessageEncoder

T = t.TypeVar("T")
R = t.TypeVar("R")
B = t.TypeVar("B")
T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)


class MessagePublisher(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def publish(self, message: T_contra) -> None:
        raise NotImplementedError


class EncodedMessagePublisher(MessagePublisher[T_contra]):
    def __init__(self, encoder: MessageEncoder[T_contra, T], publisher: MessagePublisher[T]) -> None:
        self.__encoder = encoder
        self.__publisher = publisher

    async def publish(self, message: T_contra) -> None:
        encoded_message = self.__encoder.encode(message)
        await self.__publisher.publish(encoded_message)


class MessagePublisherFactory(t.Generic[T_contra, T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_publisher(self, settings: T_contra) -> MessagePublisher[T_co]:
        raise NotImplementedError
