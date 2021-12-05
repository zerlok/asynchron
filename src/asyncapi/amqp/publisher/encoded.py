__all__ = (
    "EncodedMessagePublisher",
)

import typing as t

import aio_pika

from asyncapi.amqp.base import MessageEncoder, MessagePublisher, PublicationContext

T = t.TypeVar("T")
T_contra = t.TypeVar("T_contra", contravariant=True)


class EncodedMessagePublisher(MessagePublisher[T_contra]):
    def __init__(self, encoder: MessageEncoder[T_contra], publisher: MessagePublisher[aio_pika.Message]) -> None:
        self.__encoder = encoder
        self.__publisher = publisher

    async def publish(self, message: T_contra, context: PublicationContext) -> None:
        encoded_message = self.__encoder.encode(message, context)
        await self.__publisher.publish(encoded_message, context)