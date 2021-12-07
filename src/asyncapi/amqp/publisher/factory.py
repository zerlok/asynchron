__all__ = (
    "ExchangeBasedEncodedWithContextMessagePublisherFactory",
)

import typing as t

import aio_pika

from asyncapi.amqp.base import MessageEncoder, MessagePublisher, MessagePublisherFactory
from asyncapi.amqp.decoder.context import MessageContext, MessageContextAssigningMessageEncoder
from asyncapi.amqp.publisher.encoded import EncodedMessagePublisher
from asyncapi.amqp.publisher.exchange import ExchangeMessagePublisher

T = t.TypeVar("T")


class ExchangeBasedEncodedWithContextMessagePublisherFactory(
    MessagePublisherFactory[t.Tuple[MessageEncoder[T], aio_pika.Exchange, str, bool], T],
):
    def __init__(
            self,
            context_provider: t.Optional[t.Callable[[T], t.Optional[MessageContext]]] = None,
    ) -> None:
        self.__context_provider = context_provider

    def create_publisher(
            self,
            settings: t.Tuple[MessageEncoder[T], aio_pika.Exchange, str, bool],
    ) -> MessagePublisher[T]:
        encoder, exchange, routing_key, is_mandatory = settings

        return EncodedMessagePublisher(
            encoder=MessageContextAssigningMessageEncoder(
                encoder=encoder,
                context_provider=self.__context_provider,
            ),
            publisher=ExchangeMessagePublisher(
                exchange=exchange,
                routing_key=routing_key,
                is_mandatory=is_mandatory,
            ),
        )
