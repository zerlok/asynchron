import typing as t

import aio_pika
from pydantic import BaseModel, Protocol

from asyncapi.amqp.base import MessagePublisher, MessagePublisherFactory, PublicationContext

T = t.TypeVar("T")


class PublishersController(t.Generic[T]):
    def __init__(
            self,
            connection: aio_pika.Connection,
            publisher_factory: MessagePublisherFactory[T, aio_pika.Message],
    ) -> None:
        self.__connection = connection
        self.__publisher_factory = publisher_factory

    async def create_publisher(
            self,
            exchange_name: str,
            publisher: T,
    ) -> MessagePublisher[T]:
        return self.__publisher_factory.create_publisher(publisher)


T_model = t.TypeVar("T_model", bound=BaseModel)


class ExchangeMessagePublisher(MessagePublisher[t.Tuple[aio_pika.Message, str, bool]]):
    def __init__(self, exchange: aio_pika.Exchange) -> None:
        self.__exchange = exchange

    async def publish(self, message: t.Tuple[aio_pika.Message, str, bool], context: PublicationContext) -> None:
        amqp_message, routing_key, mandatory = message

        await self.__exchange.publish(
            message=amqp_message,
            routing_key=routing_key,
            mandatory=mandatory,
        )


class PydanticModelMessagePublisherFactory(
    MessagePublisherFactory[t.Tuple[t.Type[T_model], MessagePublisher[aio_pika.Message]], T_model],
):
    def __init__(
            self,
            protocol: Protocol = Protocol.json,
    ) -> None:
        self.__protocol = protocol

    def create_publisher(
            self,
            publisher: t.Tuple[t.Type[T_model], MessagePublisher[aio_pika.Message]],
    ) -> MessagePublisher[T_model]:
        model, amqp_publisher = publisher

        return EncodedMessagePublisher(
            encoder=PydanticModelMessageEncoder(
                model=model,
                protocol=self.__protocol,
            ),
            publisher=amqp_publisher,
        )
