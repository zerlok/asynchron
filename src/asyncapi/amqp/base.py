__all__ = (
    "AmqpContext",
    "ConsumptionContext",
    "PublicationContext",
    "MessageDecoder",
    "MessageEncoder",
    "MessageConsumer",
    "MessagePublisher",
    "MessageConsumerFactory",
    "MessagePublisherFactory",
)

import abc
import typing as t
from dataclasses import dataclass

import aio_pika

T_co = t.TypeVar("T_co", covariant=True)
T_contra = t.TypeVar("T_contra", contravariant=True)


@dataclass(frozen=True)
class AmqpContext:
    connection: aio_pika.Connection
    channel: aio_pika.Channel
    exchange: aio_pika.Exchange
    correlation_id: t.Optional[str]
    reply_to: t.Optional[str]
    user_id: t.Optional[str]
    app_id: t.Optional[str]


@dataclass(frozen=True)
class ConsumptionContext(AmqpContext):
    queue: aio_pika.Queue
    message: aio_pika.IncomingMessage


@dataclass(frozen=True)
class PublicationContext(AmqpContext):
    pass


class MessageDecoder(t.Generic[T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decode(self, message: aio_pika.IncomingMessage, context: ConsumptionContext) -> T_co:
        raise NotImplementedError


class MessageEncoder(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def encode(self, message: T_contra, context: PublicationContext) -> aio_pika.Message:
        raise NotImplementedError


class MessageConsumer(t.Generic[T_contra], metaclass=abc.ABCMeta):
    async def consume(self, message: T_contra, context: ConsumptionContext) -> None:
        raise NotImplementedError


class MessagePublisher(t.Generic[T_contra], metaclass=abc.ABCMeta):
    async def publish(self, message: T_contra, context: PublicationContext) -> None:
        raise NotImplementedError


class MessageConsumerFactory(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_consumer(self, consumer: T_contra) -> MessageConsumer[aio_pika.IncomingMessage]:
        raise NotImplementedError


class MessagePublisherFactory(t.Generic[T_contra, T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_publisher(self, publisher: T_contra) -> MessagePublisher[T_co]:
        raise NotImplementedError
