__all__ = (
    "AioPikaBasedAmqpController",
)

import typing as t

import aio_pika

from asynchron.amqp.publisher.exchange import ExchangeMessagePublisher
from asynchron.core.amqp import AmqpConsumerBindings, AmqpPublisherBindings
from asynchron.core.consumer import (
    DecodedMessageConsumer,
    MessageConsumer,
    MessageConsumerFactory,
)
from asynchron.core.controller import Controller
from asynchron.core.message import MessageDecoder, MessageEncoder
from asynchron.core.publisher import (
    EncodedMessagePublisher,
    MessagePublisher,
    MessagePublisherFactory,
)
from asynchron.strict_typing import get_or_default

T = t.TypeVar("T")
T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)


class AioPikaBasedAmqpController(
    Controller[aio_pika.IncomingMessage, AmqpConsumerBindings, aio_pika.Message, AmqpPublisherBindings],
):
    class DefaultConsumerFactory(
        MessageConsumerFactory[MessageConsumer[aio_pika.IncomingMessage], aio_pika.IncomingMessage],
    ):
        def create_consumer(
                self,
                settings: MessageConsumer[aio_pika.IncomingMessage],
        ) -> MessageConsumer[aio_pika.IncomingMessage]:
            return settings

    class DefaultPublisherFactory(MessagePublisherFactory[MessagePublisher[T], T]):
        def create_publisher(self, settings: MessagePublisher[T]) -> MessagePublisher[T]:
            return settings

    def __init__(
            self,
            connection: aio_pika.Connection,
            consumer_factory: t.Optional[MessageConsumerFactory[
                MessageConsumer[aio_pika.IncomingMessage],
                aio_pika.IncomingMessage,
            ]] = None,
            publisher_factory: t.Optional[MessagePublisherFactory[
                MessagePublisher[T],
                T,
            ]] = None,
            default_mandatory: bool = True,
    ) -> None:
        self.__connection = connection
        self.__consumer_factory = consumer_factory or self.DefaultConsumerFactory()
        self.__publisher_factory = publisher_factory or self.DefaultPublisherFactory()

        self.__default_mandatory = default_mandatory

        self.__declared_consumers: t.Dict[AmqpConsumerBindings, MessageConsumer[aio_pika.IncomingMessage]] = {}
        self.__declared_publishers: t.Dict[AmqpPublisherBindings, ExchangeMessagePublisher] = {}
        self.__consumer_tags: t.Dict[str, aio_pika.Queue] = {}

    def bind_consumer(
            self,
            decoder: MessageDecoder[aio_pika.IncomingMessage, T],
            consumer: MessageConsumer[T],
            bindings: AmqpConsumerBindings,
    ) -> MessageConsumer[aio_pika.IncomingMessage]:
        bind_consumer = self.__consumer_factory.create_consumer(DecodedMessageConsumer(
            decoder=decoder,
            consumer=consumer,
        ))

        self.__declared_consumers[bindings] = bind_consumer

        return bind_consumer

    def bind_publisher(
            self,
            encoder: MessageEncoder[T, aio_pika.Message],
            bindings: AmqpPublisherBindings,
    ) -> MessagePublisher[T]:
        exchange = self.__declared_publishers[bindings] = \
            ExchangeMessagePublisher(bindings.routing_key,
                                     get_or_default(bindings.is_mandatory, self.__default_mandatory))

        bind_publisher = self.__publisher_factory.create_publisher(EncodedMessagePublisher(
            encoder=encoder,
            publisher=exchange,
        ))

        return bind_publisher

    async def start(self) -> None:
        for publisher_bindings, publisher in self.__declared_publishers.items():
            channel = t.cast(aio_pika.Channel, await self.__connection.channel())
            await channel.set_qos(prefetch_count=publisher_bindings.prefetch_count or 0)  # type: ignore[misc]

            exchange = await channel.declare_exchange(publisher_bindings.exchange_name, publisher_bindings.exchange_type or "direct")
            publisher.attach(exchange)

        for consumer_bindings, consumer in self.__declared_consumers.items():
            channel = t.cast(aio_pika.Channel, await self.__connection.channel())
            await channel.set_qos(prefetch_count=consumer_bindings.prefetch_count or 0)  # type: ignore[misc]

            exchange = await channel.declare_exchange(consumer_bindings.exchange_name, consumer_bindings.exchange_type or "direct")
            queue = await channel.declare_queue(consumer_bindings.queue_name or "")

            for binding_key in consumer_bindings.binding_keys:
                await queue.bind(exchange, binding_key)  # type: ignore[misc]

            consumer_tag = await queue.consume(consumer.consume)
            self.__consumer_tags[consumer_tag] = queue

    async def stop(self) -> None:
        for consumer_tag, queue in self.__consumer_tags.items():
            await queue.cancel(consumer_tag)  # type: ignore[misc]
