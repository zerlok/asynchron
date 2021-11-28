__all__ = (
    "ConsumptionContext",
    "MessageConsumer",
    "MessageDecoder",
)

import abc
import typing as t
from dataclasses import dataclass

import aio_pika

T_co = t.TypeVar("T_co", covariant=True)
T_contra = t.TypeVar("T_contra", contravariant=True)


@dataclass(frozen=True)
class ConsumptionContext:
    connection: aio_pika.Connection
    channel: aio_pika.Channel
    exchange: aio_pika.Exchange
    queue: aio_pika.Queue
    message: aio_pika.IncomingMessage


class MessageConsumer(t.Generic[T_contra], metaclass=abc.ABCMeta):
    async def consume(self, message: T_contra, context: ConsumptionContext) -> None:
        raise NotImplementedError


class MessageDecoder(t.Generic[T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decode(self, message: aio_pika.IncomingMessage, context: ConsumptionContext) -> T_co:
        raise NotImplementedError
