__all__ = (
    "ConsumersController",
)

import asyncio
import functools as ft
import typing as t
from dataclasses import dataclass

import aio_pika

from asyncapi.amqp.base import ConsumptionContext, MessageConsumer, MessageConsumerFactory
from asyncapi.strict_typing import gather, gather_with_errors

T = t.TypeVar("T", bound=t.Hashable)


@dataclass(frozen=True)
class RegisteredConsumer:
    consumer: MessageConsumer[aio_pika.IncomingMessage]
    exchange_name: str
    queue_name: t.Optional[str]
    binding_keys: t.Collection[str]
    is_auto_delete_enabled: bool
    is_exclusive: bool
    is_durable: bool
    prefetch_count: int


@dataclass(frozen=True)
class ActiveConsumer:
    consumer: MessageConsumer[aio_pika.IncomingMessage]
    channel: aio_pika.Channel
    exchange: aio_pika.Exchange
    queue: aio_pika.Queue
    tag: str


class ConsumersController(t.Generic[T]):
    def __init__(
            self,
            connection: aio_pika.Connection,
            consumer_factory: MessageConsumerFactory[T],
            default_prefetch_count: int = 0,
            default_auto_delete_enabled: bool = False,
            default_exclusive: bool = False,
            default_durable: bool = False,
            loop: t.Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self.__connection = connection
        self.__consumer_factory = consumer_factory
        self.__server_name = self.__connection.kwargs.get("server_name", str(self))
        self.__default_prefetch_count = default_prefetch_count
        self.__default_auto_delete_enabled = default_auto_delete_enabled
        self.__default_exclusive = default_exclusive
        self.__default_durable = default_durable

        self.__registered_consumers: t.Dict[T, RegisteredConsumer] = {}
        self.__active_consumers: t.Dict[MessageConsumer[aio_pika.IncomingMessage], ActiveConsumer] = {}

        self.__loop = loop or asyncio.get_event_loop()
        self.__stop_waiter: asyncio.Future[bool] = self.__loop.create_future()
        self.__start_task: t.Optional[asyncio.Task[None]] = None
        self.__stop_task: t.Optional[asyncio.Task[None]] = None

    def add_consumer(
            self,
            exchange_name: str,
            binding_keys: t.Collection[str],
            consumer: T,
            queue_name: t.Optional[str] = None,
            is_auto_delete_enabled: t.Optional[bool] = None,
            is_exclusive: t.Optional[bool] = None,
            is_durable: t.Optional[bool] = None,
            prefetch_count: t.Optional[int] = None,
    ) -> None:
        if consumer in self.__registered_consumers:
            raise RuntimeError()

        self.__registered_consumers[consumer] = RegisteredConsumer(
            consumer=self.__consumer_factory.create_consumer(consumer),
            exchange_name=exchange_name,
            queue_name=queue_name,
            binding_keys=binding_keys,
            prefetch_count=prefetch_count if prefetch_count is not None else self.__default_prefetch_count,
            is_auto_delete_enabled=(
                is_auto_delete_enabled if is_auto_delete_enabled is not None else self.__default_auto_delete_enabled),
            is_exclusive=is_exclusive if is_exclusive is not None else self.__default_exclusive,
            is_durable=is_durable if is_durable is not None else self.__default_durable,
        )

    def start(self) -> None:
        self.__start_task = self.__loop.create_task(self.__start_consumers())
        self.__start_task.add_done_callback(self.__stop_on_start_error)

    def stop(self, err: t.Optional[BaseException] = None) -> None:
        if self.__start_task is not None and not self.__start_task.done():
            self.__start_task.cancel()

        if self.__stop_task is None or not self.__stop_task.done():
            return

        self.__stop_task = self.__loop.create_task(self.__stop_consumers())
        self.__stop_task.add_done_callback(self.__set_waiter)

    async def wait_for_termination(self) -> None:
        await self.__stop_waiter

    async def __start_consumers(self) -> None:
        active_consumers = await gather_with_errors(
            self.__start_consumer(registered_consumer)
            for registered_consumer in self.__registered_consumers.values()
        )

        # TODO: handle failed starts
        self.__active_consumers.update(
            (active_consumer.consumer, active_consumer)
            for active_consumer in active_consumers
            if isinstance(active_consumer, ActiveConsumer)
        )

    async def __start_consumer(
            self,
            info: RegisteredConsumer,
    ) -> ActiveConsumer:
        channel = await self.__connection.channel()
        await channel.set_qos(prefetch_count=info.prefetch_count)

        exchange = await channel.get_exchange(info.exchange_name)
        queue = await channel.declare_queue(
            name=info.queue_name,
            durable=info.is_durable,
            exclusive=info.is_exclusive,
            auto_delete=info.is_auto_delete_enabled,
        )

        await gather(
            queue.bind(exchange, binding_key)
            for binding_key in info.binding_keys
        )

        consumer_tag = await queue.consume(
            ft.partial(self.__consume, consumer=info.consumer, channel=channel, exchange=exchange, queue=queue, ))

        return ActiveConsumer(
            consumer=info.consumer,
            channel=channel,
            exchange=exchange,
            queue=queue,
            tag=consumer_tag,
        )

    async def __consume(
            self,
            message: aio_pika.IncomingMessage,
            consumer: MessageConsumer[aio_pika.IncomingMessage],
            channel: aio_pika.Channel,
            exchange: aio_pika.Exchange,
            queue: aio_pika.Queue,
    ) -> None:
        context = ConsumptionContext(
            connection=self.__connection,
            channel=channel,
            exchange=exchange,
            queue=queue,
            message=message,
            correlation_id=message.correlation_id,
            reply_to=message.reply_to,
            user_id=message.user_id,
            app_id=message.app_id,
        )

        await consumer.consume(message, context)

    async def __stop_consumers(self) -> None:
        try:
            await gather_with_errors(
                self.__stop_consumer(info)
                for info in self.__active_consumers.values()
            )

        finally:
            self.__active_consumers.clear()

    async def __stop_consumer(self, info: ActiveConsumer) -> None:
        try:
            await info.queue.cancel(info.tag)

        finally:
            await info.channel.close()  # type: ignore

    def __stop_on_start_error(self, fut: "asyncio.Future[None]") -> None:
        if not fut.cancelled() and fut.exception() is not None:
            self.stop(fut.exception())

    def __set_waiter(self, fut: "asyncio.Future[None]") -> None:
        error = fut.exception()
        if error is not None:
            self.__stop_waiter.set_exception(error)

        self.__stop_waiter.set_result(True)
