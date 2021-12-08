import asyncio
import typing as t
from dataclasses import dataclass
from weakref import WeakKeyDictionary, WeakValueDictionary

import aio_pika

from asynchron.amqp.base import MessagePublisher, MessagePublisherFactory
from asynchron.strict_typing import get_or_default

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
            publisher_factory: MessagePublisherFactory[t.Tuple[T_contra, aio_pika.Exchange, str, bool], T_co],
            default_exchange_name: str = "default",
            default_exchange_type: ExchangeType = "direct",
            default_auto_delete: bool = True,
            default_durable: bool = False,
            default_mandatory: bool = True,
            prefetch_count: int = 0,
    ) -> None:
        self.__connection = connection
        self.__publisher_factory = publisher_factory
        self.__default_exchange_name = default_exchange_name
        self.__default_exchange_type = default_exchange_type
        self.__default_auto_delete = default_auto_delete
        self.__default_durable = default_durable
        self.__default_mandatory = default_mandatory
        self.__prefetch_count = prefetch_count

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
            publisher: T_contra,
            routing_key: str,
            exchange_name: t.Optional[str] = None,
            exchange_type: t.Optional[ExchangeType] = None,
            is_auto_delete_enabled: t.Optional[bool] = None,
            is_durable: t.Optional[bool] = None,
            is_mandatory: t.Optional[bool] = None,
            prefetch_count: t.Optional[int] = None,
    ) -> MessagePublisher[T_co]:
        publisher_exchange = get_or_default(exchange_name, self.__default_exchange_name)
        publisher_key = (publisher_exchange, routing_key, publisher,)

        async with self.__locks.provide(publisher_key):
            registered_publisher = self.__registered_publishers.get(publisher_key)
            if not registered_publisher:
                channel = await self.__connection.channel()
                await channel.set_qos(prefetch_count=prefetch_count)

                exchange = await channel.declare_exchange(
                    name=publisher_exchange,
                    type=get_or_default(exchange_type, self.__default_exchange_type),
                    durable=get_or_default(is_durable, self.__default_durable),
                    auto_delete=get_or_default(is_auto_delete_enabled, self.__default_auto_delete),
                )

                # declared_publisher = DeclaredPublisher(
                #     publisher=publisher,
                #     channel=channel,
                #     exchange=exchange,
                #     routing_key=routing_key,
                #     is_auto_delete_enabled=is_auto_delete_enabled if is_auto_delete_enabled is not None else True,
                #     is_durable=is_durable if is_durable is not None else False,
                #     is_mandatory=is_mandatory if is_mandatory is not None else True,
                #     prefetch_count=prefetch_count if prefetch_count is not None else 0,
                # )

                registered_publisher = self.__registered_publishers[
                    publisher_key] = self.__publisher_factory.create_publisher(
                    (publisher, exchange, routing_key, get_or_default(is_mandatory, self.__default_mandatory)))

        return registered_publisher
