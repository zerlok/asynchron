import asyncio
import typing as t
from dataclasses import dataclass
from weakref import WeakKeyDictionary, WeakValueDictionary

import aio_pika

from asyncapi.amqp.base import MessagePublisher, MessagePublisherFactory

T = t.TypeVar("T")
K = t.TypeVar("K", bound=t.Hashable)
V = t.TypeVar("V")
T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)

ExchangeType = t.Literal["fanout", "direct", "topic", "headers", "x-delayed-message", "x-consistent-hash",
                         "x-modulus-hash"]


@dataclass(frozen=True)
class DeclaredPublisher(t.Generic[T]):
    publisher: T
    channel: aio_pika.Channel
    exchange: aio_pika.Exchange
    routing_key: str
    is_auto_delete_enabled: bool
    is_durable: bool
    is_mandatory: bool
    prefetch_count: int


class WeakCachedValueProvider(t.Generic[K, V]):
    def __init__(self, provider: t.Callable[[K], V]) -> None:
        self.__provider = provider
        self.__provided: WeakKeyDictionary[K, V] = WeakKeyDictionary({})

    def provide(self, key: K) -> V:
        provided = self.__provided.get(key)
        if not provided:
            provided = self.__provided[key] = self.__provider(key)

        return provided


class PublishersController(t.Generic[T_contra, T_co]):
    def __init__(
            self,
            connection: aio_pika.Connection,
            publisher_factory: MessagePublisherFactory[DeclaredPublisher[T_contra], T_co],
    ) -> None:
        self.__connection = connection
        self.__publisher_factory = publisher_factory

        self.__registered_publishers: WeakValueDictionary[t.Tuple[str, str, T_contra], MessagePublisher[T_co]] \
            = WeakValueDictionary({})
        self.__declared_publishers: WeakKeyDictionary[MessagePublisher[T_co], DeclaredPublisher[T_contra]] \
            = WeakKeyDictionary({})

        @WeakCachedValueProvider
        def provide_lock(key: t.Tuple[str, str, T_contra]) -> asyncio.Lock:
            return asyncio.Lock()

        self.__locks = provide_lock

    async def create_publisher(
            self,
            exchange_name: str,
            exchange_type: ExchangeType,
            routing_key: str,
            publisher: T_contra,
            is_auto_delete_enabled: t.Optional[bool] = None,
            is_durable: t.Optional[bool] = None,
            is_mandatory: t.Optional[bool] = None,
            prefetch_count: t.Optional[int] = None,
    ) -> MessagePublisher[T_co]:
        publisher_key = (exchange_name, routing_key, publisher,)

        async with self.__locks.provide(publisher_key):
            registered_publisher = self.__registered_publishers.get(publisher_key)
            if not registered_publisher:
                channel = await self.__connection.channel()
                await channel.set_qos(prefetch_count=prefetch_count)

                exchange = await channel.declare_exchange(
                    name=exchange_name,
                    type=exchange_type,
                    durable=is_durable,
                    auto_delete=is_auto_delete_enabled,
                )

                declared_publisher = DeclaredPublisher(
                    publisher=publisher,
                    channel=channel,
                    exchange=exchange,
                    routing_key=routing_key,
                    is_auto_delete_enabled=is_auto_delete_enabled if is_auto_delete_enabled is not None else True,
                    is_durable=is_durable if is_durable is not None else False,
                    is_mandatory=is_mandatory if is_mandatory is not None else True,
                    prefetch_count=prefetch_count if prefetch_count is not None else 0,
                )

                registered_publisher = self.__registered_publishers[publisher_key] = \
                    self.__publisher_factory.create_publisher(declared_publisher)

        return registered_publisher
