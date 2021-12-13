__all__ = (
    "AioPikaBasedAmqpController",
)

import typing as t

import aio_pika

from asynchron.amqp.connector import AmqpConnector
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
    class DefaultConsumerFactory(MessageConsumerFactory[MessageConsumer[T], T]):
        def create_consumer(self, settings: MessageConsumer[T]) -> MessageConsumer[T]:
            return settings

    class DefaultPublisherFactory(MessagePublisherFactory[MessagePublisher[T], T]):
        def create_publisher(self, settings: MessagePublisher[T]) -> MessagePublisher[T]:
            return settings

    def __init__(
            self,
            connector: AmqpConnector,
            consumer_factory: t.Optional[MessageConsumerFactory[MessageConsumer[T], T]] = None,
            publisher_factory: t.Optional[MessagePublisherFactory[MessagePublisher[T], T]] = None,
            default_mandatory: bool = True,
    ) -> None:
        self.__connector = connector
        self.__consumer_factory: MessageConsumerFactory[MessageConsumer[T], T] \
            = consumer_factory or self.DefaultConsumerFactory()
        self.__publisher_factory: MessagePublisherFactory[MessagePublisher[T], T] \
            = publisher_factory or self.DefaultPublisherFactory()

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
        result = self.__declared_consumers[bindings] = DecodedMessageConsumer(
            decoder=decoder,
            consumer=self.__consumer_factory.create_consumer(consumer),
        )

        return result

    def bind_publisher(
            self,
            encoder: MessageEncoder[T, aio_pika.Message],
            bindings: AmqpPublisherBindings,
    ) -> MessagePublisher[T]:
        exchange = self.__declared_publishers[bindings] = \
            ExchangeMessagePublisher(bindings.routing_key,
                                     get_or_default(bindings.is_mandatory, self.__default_mandatory))

        return self.__publisher_factory.create_publisher(EncodedMessagePublisher(
            encoder=encoder,
            publisher=exchange,
        ))

    async def start(self) -> None:
        for publisher_bindings, publisher in self.__declared_publishers.items():
            _, exchange = await self.__connector.create_exchange(
                exchange_name=publisher_bindings.exchange_name,
                exchange_type=publisher_bindings.exchange_type,
                prefetch_count=publisher_bindings.prefetch_count,
            )
            publisher.attach(exchange)

        for consumer_bindings, consumer in self.__declared_consumers.items():
            _, queue, consumer_tag = await self.__connector.create_consumer(
                consumer=consumer.consume,
                binding_keys=consumer_bindings.binding_keys,
                exchange_name=consumer_bindings.exchange_name,
                exchange_type=consumer_bindings.exchange_type,
                queue_name=consumer_bindings.queue_name,
                prefetch_count=consumer_bindings.prefetch_count,
            )
            self.__consumer_tags[consumer_tag] = queue

    async def stop(self) -> None:
        for consumer_tag, queue in self.__consumer_tags.items():
            await self.__connector.remove_consumer(queue, consumer_tag)
