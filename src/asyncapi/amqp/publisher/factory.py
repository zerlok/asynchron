__all__ = (
    "PydanticModelMessagePublisherFactory",
    "ExchangeBasedEncodedMessagePublisherFactory",
)

import typing as t

import aio_pika
from pydantic import BaseModel, Protocol

from asyncapi.amqp.base import MessagePublisher, MessagePublisherFactory
from asyncapi.amqp.decoder.pydantic import PydanticModelMessageEncoder
from asyncapi.amqp.publisher.controller import DeclaredPublisher
from asyncapi.amqp.publisher.encoded import EncodedMessagePublisher
from asyncapi.amqp.publisher.exchange import ExchangeMessagePublisher

T = t.TypeVar("T")
T_model = t.TypeVar("T_model", bound=BaseModel)
T_contra = t.TypeVar("T_contra", contravariant=True)
T_co = t.TypeVar("T_co", covariant=True)


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


class ExchangeBasedEncodedMessagePublisherFactory(
    MessagePublisherFactory[DeclaredPublisher[T_contra], T_co],
):
    def __init__(
            self,
            factory: MessagePublisherFactory[t.Tuple[T_contra, MessagePublisher[aio_pika.Message]], T_co],
    ) -> None:
        self.__factory = factory

    def create_publisher(self, publisher: DeclaredPublisher[T_contra]) -> MessagePublisher[T_co]:
        amqp_publisher = ExchangeMessagePublisher(
            exchange=publisher.exchange,
            routing_key=publisher.routing_key,
            is_mandatory=publisher.is_mandatory,
        )

        return self.__factory.create_publisher((publisher.publisher, amqp_publisher))
