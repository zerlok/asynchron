__all__ = (
    "ConsumptionContext",
)

import typing as t
from dataclasses import dataclass

import aio_pika

T = t.TypeVar("T")


@dataclass(frozen=True)
class ConsumptionContext(t.Generic[T]):
    connection: aio_pika.Connection
    channel: aio_pika.Channel
    exchange: aio_pika.Exchange
    queue: aio_pika.Queue
    message: T
