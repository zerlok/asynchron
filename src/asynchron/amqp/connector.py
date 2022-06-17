__all__ = (
    "AmqpConnector",
)

import abc
import asyncio
import typing as t
from types import TracebackType

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
)

from asynchron.core.amqp import AmqpServerBindings
from asynchron.core.consumer import MessageConsumerFunc

T = t.TypeVar("T")


class AmqpConnector(t.AsyncContextManager["AmqpConnector"], metaclass=abc.ABCMeta):
    def __init__(
            self,
            bindings: AmqpServerBindings,
    ) -> None:
        self.__bindings = bindings

        self.__lock: t.Optional[asyncio.Lock] = None
        self.__connection: t.Optional[AbstractRobustConnection] = None

    async def __aenter__(self) -> "AmqpConnector":
        lock = self.__lock = (self.__lock or asyncio.Lock())

        async with lock:
            if self.__connection is None:
                self.__connection = await aio_pika.connect_robust(self.__bindings.connection_url)

        return self

    async def __aexit__(
            self,
            __exc_type: t.Optional[t.Type[BaseException]],
            __exc_value: t.Optional[BaseException],
            __traceback: t.Optional[TracebackType],
    ) -> t.Optional[bool]:
        if self.__connection is not None:
            connection, self.__connection = self.__connection, None

            if __exc_type is not None:
                await connection.close(__exc_type)

            else:
                await connection.close()

        return None

    async def create_channel(self, prefetch_count: t.Optional[int]) -> AbstractChannel:
        if self.__connection is None:
            raise RuntimeError()

        channel = await self.__connection.channel()
        await channel.set_qos(prefetch_count=prefetch_count or 0)

        return channel

    async def create_exchange(
            self,
            exchange_name: t.Optional[str] = None,
            exchange_type: t.Optional[t.Literal["fanout", "direct", "topic", "headers"]] = None,
            prefetch_count: t.Optional[int] = None,
    ) -> t.Tuple[AbstractChannel, AbstractExchange]:
        channel = await self.create_channel(prefetch_count)

        exchange = await channel.declare_exchange(exchange_name or "", exchange_type or "direct")

        return channel, exchange

    async def create_consumer(
            self,
            consumer: MessageConsumerFunc[AbstractIncomingMessage],
            binding_keys: t.Collection[str],
            exchange_name: t.Optional[str] = None,
            exchange_type: t.Optional[t.Literal["fanout", "direct", "topic", "headers"]] = None,
            queue_name: t.Optional[str] = None,
            prefetch_count: t.Optional[int] = None,
    ) -> t.Tuple[AbstractChannel, AbstractQueue, str]:
        channel, exchange = await self.create_exchange(
            exchange_name=exchange_name,
            exchange_type=exchange_type,
            prefetch_count=prefetch_count,
        )

        queue = await channel.declare_queue(queue_name or "")

        for binding_key in binding_keys:
            await queue.bind(exchange, binding_key)

        consumer_tag = await queue.consume(consumer)

        return channel, queue, consumer_tag

    async def remove_consumer(
            self,
            queue: AbstractQueue,
            consumer_tag: str,
    ) -> None:
        await queue.cancel(consumer_tag)
