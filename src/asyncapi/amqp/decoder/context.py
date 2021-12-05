__all__ = (
    "PublicationContextAssigningMessageEncoder",
)

import typing as t

import aio_pika

from asyncapi.amqp.base import MessageEncoder, PublicationContext

T_contra = t.TypeVar("T_contra", contravariant=True)


class PublicationContextAssigningMessageEncoder(MessageEncoder[T_contra]):

    def __init__(
            self,
            encoder: MessageEncoder[T_contra],
    ) -> None:
        self.__encoder = encoder

    def encode(self, message: T_contra, context: PublicationContext) -> aio_pika.Message:
        encoded_message = self.__encoder.encode(message, context)

        if context.correlation_id is not None:
            encoded_message.correlation_id = context.correlation_id

        if context.reply_to is not None:
            encoded_message.reply_to = context.reply_to

        if context.user_id is not None:
            encoded_message.user_id = context.user_id

        if context.app_id is not None:
            encoded_message.app_id = context.app_id

        return encoded_message
